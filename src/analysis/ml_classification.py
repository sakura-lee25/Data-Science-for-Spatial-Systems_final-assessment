"""Random Forest classification for high-risk MSOA identification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    average_precision_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from src.utils.config import (
    FIGURES_DIR,
    HIGH_RISK_PERCENTILE,
    MSOA_ANALYSIS_GPKG,
    TABLES_DIR,
)

# Features used for classification
FEATURE_COLS = [
    "imd_score",
    "junction_density",
    "road_density",
    "urban_pct",
    "dark_pct",
    "wet_road_pct",
    "road_length_km",
    "population",
]


def create_labels(
    gdf: gpd.GeoDataFrame,
    percentile: float | None = None,
    rate_col: str = "accident_rate_per_10k",
) -> gpd.GeoDataFrame:
    """Create binary high-risk labels based on accident rate percentile.

    Args:
        gdf: MSOA-level GeoDataFrame.
        percentile: Percentile threshold for high-risk. Defaults to config.
        rate_col: Column with accident rate.

    Returns:
        GeoDataFrame with 'high_risk' column (1 = high risk, 0 = low risk).
    """
    percentile = percentile or HIGH_RISK_PERCENTILE
    threshold = np.percentile(gdf[rate_col].dropna(), percentile)

    gdf = gdf.copy()
    gdf["high_risk"] = (gdf[rate_col] >= threshold).astype(int)

    n_pos = gdf["high_risk"].sum()
    n_neg = len(gdf) - n_pos
    logger.info(
        f"High-risk threshold: {threshold:.2f} (top {100 - percentile:.0f}%)\n"
        f"  Positive: {n_pos:,} ({n_pos / len(gdf) * 100:.1f}%)\n"
        f"  Negative: {n_neg:,} ({n_neg / len(gdf) * 100:.1f}%)"
    )
    return gdf


def spatial_block_split(
    gdf: gpd.GeoDataFrame,
    n_blocks: int = 5,
    random_state: int = 42,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create spatial block cross-validation splits to prevent spatial leakage.

    Divides the study area into spatial blocks based on MSOA centroids,
    ensuring that nearby areas are in the same fold.

    Args:
        gdf: GeoDataFrame with geometry.
        n_blocks: Number of spatial blocks (folds).
        random_state: Random seed.

    Returns:
        List of (train_idx, test_idx) tuples.
    """
    from sklearn.cluster import KMeans

    centroids = np.column_stack([
        gdf.geometry.centroid.x,
        gdf.geometry.centroid.y,
    ])

    kmeans = KMeans(n_clusters=n_blocks, random_state=random_state, n_init=10)
    block_labels = kmeans.fit_predict(centroids)

    splits = []
    for fold in range(n_blocks):
        test_mask = block_labels == fold
        train_idx = np.where(~test_mask)[0]
        test_idx = np.where(test_mask)[0]
        splits.append((train_idx, test_idx))
        logger.debug(
            f"Fold {fold}: train={len(train_idx):,}, test={len(test_idx):,}"
        )

    return splits


def train_random_forest(
    gdf: gpd.GeoDataFrame,
    features: list[str] | None = None,
    use_smote: bool = True,
    spatial_cv: bool = True,
    n_folds: int = 5,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train Random Forest classifier with SMOTE and spatial CV.

    Args:
        gdf: GeoDataFrame with features and high_risk label.
        features: Feature column names.
        use_smote: Apply SMOTE oversampling.
        spatial_cv: Use spatial block CV instead of random CV.
        n_folds: Number of CV folds.
        random_state: Random seed.

    Returns:
        Dictionary with model, predictions, and evaluation metrics.
    """
    features = features or FEATURE_COLS
    available = [f for f in features if f in gdf.columns]
    if len(available) < len(features):
        logger.warning(f"Missing features: {set(features) - set(available)}")

    # Prepare data
    data = gdf[available + ["high_risk"]].dropna()
    X = data[available].values
    y = data["high_risk"].values

    logger.info(f"Training data: {len(X):,} samples, {len(available)} features")
    logger.info(f"Class balance: {np.sum(y == 1):,} positive / {np.sum(y == 0):,} negative")

    # Cross-validation splits
    if spatial_cv:
        splits = spatial_block_split(gdf.loc[data.index], n_blocks=n_folds)
    else:
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_state)
        splits = list(skf.split(X, y))

    # Cross-validated predictions
    y_pred_proba = np.zeros(len(y))
    y_pred = np.zeros(len(y), dtype=int)
    fold_scores = []

    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Apply SMOTE to training set only
        if use_smote:
            from imblearn.over_sampling import SMOTE

            smote = SMOTE(random_state=random_state)
            X_train, y_train = smote.fit_resample(X_train, y_train)

        # Train model
        rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=15,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )
        rf.fit(X_train, y_train)

        # Predict
        y_pred_proba[test_idx] = rf.predict_proba(X_test)[:, 1]
        y_pred[test_idx] = rf.predict(X_test)

        fold_f1 = f1_score(y_test, y_pred[test_idx])
        fold_scores.append(fold_f1)
        logger.info(f"Fold {fold_idx}: F1 = {fold_f1:.3f}")

    # Final model trained on all data (with SMOTE)
    if use_smote:
        from imblearn.over_sampling import SMOTE

        smote = SMOTE(random_state=random_state)
        X_resampled, y_resampled = smote.fit_resample(X, y)
    else:
        X_resampled, y_resampled = X, y

    final_rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )
    final_rf.fit(X_resampled, y_resampled)

    # Feature importance
    importance = pd.DataFrame({
        "feature": available,
        "importance": final_rf.feature_importances_,
    }).sort_values("importance", ascending=False)

    # Evaluation metrics
    cm = confusion_matrix(y, y_pred)
    report = classification_report(y, y_pred, output_dict=True)

    # Precision-recall curve
    precision, recall, thresholds = precision_recall_curve(y, y_pred_proba)
    avg_precision = average_precision_score(y, y_pred_proba)

    logger.info(f"Mean CV F1: {np.mean(fold_scores):.3f} ± {np.std(fold_scores):.3f}")
    logger.info(f"Average Precision: {avg_precision:.3f}")
    logger.info(f"\nFeature importance:\n{importance.to_string(index=False)}")

    result = {
        "model": final_rf,
        "feature_names": available,
        "feature_importance": importance,
        "y_true": y,
        "y_pred": y_pred,
        "y_pred_proba": y_pred_proba,
        "confusion_matrix": cm,
        "classification_report": report,
        "precision": precision,
        "recall": recall,
        "pr_thresholds": thresholds,
        "avg_precision": avg_precision,
        "fold_f1_scores": fold_scores,
        "mean_f1": np.mean(fold_scores),
    }

    return result


def run_ml_classification(
    gpkg_path: Path | None = None,
) -> dict[str, Any]:
    """Run the complete ML classification pipeline.

    Args:
        gpkg_path: Path to MSOA analysis GeoPackage.

    Returns:
        Dictionary with all classification results.
    """
    gpkg_path = gpkg_path or MSOA_ANALYSIS_GPKG

    logger.info("=" * 50)
    logger.info("Running ML classification pipeline")
    logger.info("=" * 50)

    gdf = gpd.read_file(gpkg_path)
    gdf = gdf[gdf["accident_rate_per_10k"] > 0].copy()
    logger.info(f"Loaded {len(gdf):,} MSOAs")

    # Create labels
    gdf = create_labels(gdf)

    # Train and evaluate
    results = train_random_forest(gdf)

    # Save results
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    results["feature_importance"].to_csv(
        TABLES_DIR / "feature_importance.csv", index=False
    )

    report_df = pd.DataFrame(results["classification_report"]).T
    report_df.to_csv(TABLES_DIR / "classification_report.csv")

    cm_df = pd.DataFrame(
        results["confusion_matrix"],
        index=["Actual Low", "Actual High"],
        columns=["Predicted Low", "Predicted High"],
    )
    cm_df.to_csv(TABLES_DIR / "confusion_matrix.csv")

    logger.success("ML classification pipeline complete")
    return results


if __name__ == "__main__":
    run_ml_classification()
