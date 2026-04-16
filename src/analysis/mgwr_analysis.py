"""Multi-scale Geographically Weighted Regression (MGWR) analysis."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.utils.config import (
    CACHE_DIR,
    CRS_OSGB,
    FIGURES_DIR,
    MGWR_COEFFICIENTS_GPKG,
    MSOA_ANALYSIS_GPKG,
    TABLES_DIR,
    ensure_file,
)


# ── Variable configuration ────────────────────────────────────
DEPENDENT_VAR = "log_accident_rate"
INDEPENDENT_VARS = [
    "imd_score",
    'infra_index',
    "dark_pct",
    "wet_road_pct",
]


def check_vif(
    gdf: gpd.GeoDataFrame,
    variables: list[str] | None = None,
    threshold: float = 10.0,
) -> pd.DataFrame:
    """Check multicollinearity using Variance Inflation Factor.

    Args:
        gdf: GeoDataFrame with feature columns.
        variables: Independent variables to check. Defaults to INDEPENDENT_VARS.
        threshold: VIF threshold for concern (typically 5-10).

    Returns:
        DataFrame with VIF values per variable.
    """
    variables = variables or INDEPENDENT_VARS
    X = gdf[variables].dropna().values

    vif_data = pd.DataFrame({
        "variable": variables,
        "VIF": [variance_inflation_factor(X, i) for i in range(X.shape[1])],
    })
    vif_data["concern"] = vif_data["VIF"] > threshold

    logger.info(f"VIF check (threshold={threshold}):\n{vif_data.to_string(index=False)}")

    high_vif = vif_data[vif_data["concern"]]
    if not high_vif.empty:
        logger.warning(
            f"High VIF detected: {high_vif['variable'].tolist()}. "
            "Consider removing or combining variables."
        )

    return vif_data


def run_ols_baseline(
    gdf: gpd.GeoDataFrame,
    dep_var: str | None = None,
    indep_vars: list[str] | None = None,
) -> dict[str, Any]:
    """Run OLS regression as baseline for comparison with GWR/MGWR.

    Also tests residuals for spatial autocorrelation using Moran's I
    to justify the need for geographically weighted regression.

    Args:
        gdf: GeoDataFrame with all variables.
        dep_var: Dependent variable name.
        indep_vars: Independent variable names.

    Returns:
        Dictionary with OLS results and residual Moran's I.
    """
    import statsmodels.api as sm
    from esda.moran import Moran
    from libpysal.weights import Queen

    dep_var = dep_var or DEPENDENT_VAR
    indep_vars = indep_vars or INDEPENDENT_VARS

    # Prepare data
    data = gdf[indep_vars + [dep_var]].dropna()
    y = data[dep_var].values
    X = sm.add_constant(data[indep_vars].values)

    # Fit OLS
    model = sm.OLS(y, X).fit()
    logger.info(f"OLS R² = {model.rsquared:.4f}, Adj R² = {model.rsquared_adj:.4f}")
    logger.info(f"OLS AIC = {model.aic:.1f}")

    # Test residual spatial autocorrelation
    gdf_clean = gdf.loc[data.index].copy()
    gdf_clean["ols_residual"] = model.resid

    w = Queen.from_dataframe(gdf_clean, use_index=False)
    w.transform = "r"
    mi = Moran(model.resid, w, permutations=999)

    logger.info(
        f"Residual Moran's I = {mi.I:.4f}, p = {mi.p_sim:.4f} "
        f"({'significant' if mi.p_sim < 0.05 else 'not significant'})"
    )

    result = {
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "aic": model.aic,
        "coefficients": dict(zip(["constant"] + indep_vars, model.params)),
        "p_values": dict(zip(["constant"] + indep_vars, model.pvalues)),
        "residual_moran_I": mi.I,
        "residual_moran_p": mi.p_sim,
        "n_obs": len(y),
    }

    return result


def run_mgwr(
    gdf: gpd.GeoDataFrame,
    dep_var: str | None = None,
    indep_vars: list[str] | None = None,
    cache: bool = True,
) -> dict[str, Any]:
    """Fit a Multi-scale Geographically Weighted Regression model.

    MGWR allows each variable to have its own spatial bandwidth,
    capturing different spatial scales of influence.

    NOTE: This can take 2-4 hours for ~6,800 observations.
    Results are cached to avoid re-computation.

    Args:
        gdf: GeoDataFrame with all variables.
        dep_var: Dependent variable name.
        indep_vars: Independent variable names.
        cache: Whether to cache/load results.

    Returns:
        Dictionary with MGWR results, bandwidths, and local coefficients.
    """
    from mgwr.gwr import GWR, MGWR
    from mgwr.sel_bw import Sel_BW

    dep_var = dep_var or DEPENDENT_VAR
    indep_vars = indep_vars or INDEPENDENT_VARS

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / "mgwr_results.pkl"

    cache_path = ensure_file(cache_path)
    if cache and cache_path.exists():
        logger.info(f"Loading cached MGWR results from {cache_path}")
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    # Prepare data
    data = gdf[indep_vars + [dep_var, "geometry"]].dropna()
    coords = np.column_stack([data.geometry.centroid.x, data.geometry.centroid.y])
    y = data[dep_var].values.reshape(-1, 1)
    X = data[indep_vars].values

    # Standardise X for MGWR
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_std[X_std == 0] = 1
    X_scaled = (X - X_mean) / X_std

    n = len(y)
    logger.info(f"Fitting MGWR with {n} observations, {len(indep_vars)} variables")
    logger.info("This may take several hours...")

    # ── GWR bandwidth selection (for comparison) ──────────────
    logger.info("Selecting GWR bandwidth...")
    gwr_selector = Sel_BW(coords, y, X_scaled, kernel="bisquare", fixed=False)
    gwr_bw = gwr_selector.search(criterion="AICc")
    logger.info(f"GWR optimal bandwidth: {gwr_bw}")

    # Fit GWR
    gwr_model = GWR(coords, y, X_scaled, bw=gwr_bw, kernel="bisquare", fixed=False)
    gwr_results = gwr_model.fit()
    logger.info(f"GWR R² = {gwr_results.R2:.4f}, AICc = {gwr_results.aicc:.1f}")

    # ── MGWR bandwidth selection ──────────────────────────────
    logger.info("Selecting MGWR bandwidths (this is the slow step)...")
    mgwr_selector = Sel_BW(coords, y, X_scaled, multi=True, kernel="bisquare", fixed=False)
    mgwr_bw = mgwr_selector.search(criterion="AICc")
    logger.info(f"MGWR bandwidths: {mgwr_bw}")

    # Fit MGWR
    mgwr_model = MGWR(coords, y, X_scaled, mgwr_selector, kernel="bisquare", fixed=False)
    mgwr_results = mgwr_model.fit()
    logger.info(f"MGWR R² = {mgwr_results.R2:.4f}, AICc = {mgwr_results.aicc:.1f}")

    # Extract local coefficients
    coef_names = ["intercept"] + indep_vars
    local_coefficients = pd.DataFrame(
        mgwr_results.params,
        columns=coef_names,
        index=data.index,
    )

    # Local t-values for significance testing
    local_tvalues = pd.DataFrame(
        mgwr_results.tvalues,
        columns=[f"{c}_tval" for c in coef_names],
        index=data.index,
    )

    # Build coefficient GeoDataFrame
    coef_gdf = gpd.GeoDataFrame(
        pd.concat([local_coefficients, local_tvalues], axis=1),
        geometry=data.geometry.values,
        crs=CRS_OSGB,
    )
    coef_gdf["msoa_code"] = gdf.loc[data.index, "msoa_code"].values

    # Save coefficient surface
    coef_gdf.to_file(MGWR_COEFFICIENTS_GPKG, driver="GPKG")
    logger.info(f"Saved MGWR coefficients: {MGWR_COEFFICIENTS_GPKG}")

    result = {
        "gwr_r2": gwr_results.R2,
        "gwr_aicc": gwr_results.aicc,
        "gwr_bw": gwr_bw,
        "mgwr_r2": mgwr_results.R2,
        "mgwr_aicc": mgwr_results.aicc,
        "mgwr_bw": list(mgwr_bw),
        "variable_names": coef_names,
        "coef_gdf": coef_gdf,
        "coef_summary": local_coefficients.describe(),
        "n_obs": n,
    }

    # Cache results
    if cache:
        with open(cache_path, "wb") as f:
            pickle.dump(result, f)
        logger.info(f"Cached MGWR results: {cache_path}")

    logger.success("MGWR analysis complete")
    return result


def run_mgwr_analysis(
    gpkg_path: Path | None = None,
) -> dict[str, Any]:
    """Run the complete MGWR analysis pipeline.

    Steps:
        1. VIF multicollinearity check
        2. OLS baseline regression
        3. MGWR fitting

    Args:
        gpkg_path: Path to MSOA analysis GeoPackage.

    Returns:
        Dictionary with all analysis results.
    """
    gpkg_path = gpkg_path or MSOA_ANALYSIS_GPKG
    gpkg_path = ensure_file(gpkg_path)

    logger.info("=" * 50)
    logger.info("Running MGWR analysis pipeline")
    logger.info("=" * 50)

    gdf = gpd.read_file(gpkg_path)
    gdf = gdf[gdf["accident_rate_per_10k"] > 0].copy()
    logger.info(f"Loaded {len(gdf):,} MSOAs")

    # Step 1: VIF check
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    vif_df = check_vif(gdf)
    vif_df.to_csv(TABLES_DIR / "vif_check.csv", index=False)

    # Step 2: OLS baseline
    ols_results = run_ols_baseline(gdf)

    # Save OLS summary
    ols_summary = pd.DataFrame({
        "variable": list(ols_results["coefficients"].keys()),
        "coefficient": list(ols_results["coefficients"].values()),
        "p_value": list(ols_results["p_values"].values()),
    })
    ols_summary.to_csv(TABLES_DIR / "ols_summary.csv", index=False)

    # Step 3: MGWR
    mgwr_results = run_mgwr(gdf)

    # Save bandwidth comparison
    bw_summary = pd.DataFrame({
        "variable": mgwr_results["variable_names"],
        "mgwr_bandwidth": ["-"] + [str(b) for b in mgwr_results["mgwr_bw"]],
    })
    bw_summary.to_csv(TABLES_DIR / "mgwr_bandwidths.csv", index=False)

    all_results = {
        "vif": vif_df,
        "ols": ols_results,
        "mgwr": mgwr_results,
    }

    logger.success("MGWR analysis pipeline complete")
    return all_results


if __name__ == "__main__":
    run_mgwr_analysis()
