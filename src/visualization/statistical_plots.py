"""Statistical plots for academic publication: Moran scatter, PR curve, etc."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger

from src.utils.config import FIGURE_DPI, FIGURES_DIR


# Academic style
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.bbox": "tight",
    "savefig.dpi": FIGURE_DPI,
})


def plot_moran_scatter(
    y: np.ndarray,
    w_y: np.ndarray,
    moran_I: float,
    p_value: float,
    variable_name: str = "Accident Rate",
    filename: str = "fig02_moran_scatter.png",
    figsize: tuple[float, float] = (8, 7),
) -> Path:
    """Create Moran's I scatter plot (standardised variable vs spatial lag).

    Args:
        y: Observed values (standardised).
        w_y: Spatial lag values (standardised).
        moran_I: Global Moran's I statistic.
        p_value: p-value for Moran's I.
        variable_name: Name for axis labels.
        filename: Output filename.
        figsize: Figure dimensions.

    Returns:
        Path to saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(y, w_y, s=5, alpha=0.4, color="#4477AA", edgecolor="none")

    # Best fit line
    m, b = np.polyfit(y, w_y, 1)
    x_line = np.linspace(y.min(), y.max(), 100)
    ax.plot(x_line, m * x_line + b, color="#CC3311", linewidth=1.5)

    # Reference lines
    ax.axhline(0, color="grey", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="grey", linewidth=0.5, linestyle="--")

    # Quadrant labels
    ax.text(0.95, 0.95, "HH", transform=ax.transAxes, ha="right", va="top",
            fontsize=14, color="#d7191c", fontweight="bold", alpha=0.6)
    ax.text(0.05, 0.05, "LL", transform=ax.transAxes, ha="left", va="bottom",
            fontsize=14, color="#2c7bb6", fontweight="bold", alpha=0.6)
    ax.text(0.95, 0.05, "HL", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=14, color="#fdae61", fontweight="bold", alpha=0.6)
    ax.text(0.05, 0.95, "LH", transform=ax.transAxes, ha="left", va="top",
            fontsize=14, color="#abd9e9", fontweight="bold", alpha=0.6)

    ax.set_xlabel(f"Standardised {variable_name}")
    ax.set_ylabel(f"Spatial Lag of {variable_name}")
    ax.set_title(
        f"Moran's I Scatter Plot\n"
        f"I = {moran_I:.4f}, p = {p_value:.4f}",
        fontweight="bold",
    )

    dest = FIGURES_DIR / filename
    fig.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved: {dest}")
    return dest


def plot_pr_curve(
    precision: np.ndarray,
    recall: np.ndarray,
    avg_precision: float,
    filename: str = "fig07_pr_curve.png",
    figsize: tuple[float, float] = (8, 7),
) -> Path:
    """Create Precision-Recall curve.

    Args:
        precision: Precision values.
        recall: Recall values.
        avg_precision: Average precision score.
        filename: Output filename.
        figsize: Figure dimensions.

    Returns:
        Path to saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(recall, precision, color="#4477AA", linewidth=2)
    ax.fill_between(recall, precision, alpha=0.15, color="#4477AA")

    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(
        f"Precision-Recall Curve\n"
        f"Average Precision = {avg_precision:.3f}",
        fontweight="bold",
    )
    ax.set_xlim([0, 1.01])
    ax.set_ylim([0, 1.01])
    ax.grid(True, alpha=0.3)

    dest = FIGURES_DIR / filename
    fig.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved: {dest}")
    return dest


def plot_confusion_matrix(
    cm: np.ndarray,
    labels: list[str] | None = None,
    filename: str = "fig08_confusion_matrix.png",
    figsize: tuple[float, float] = (7, 6),
) -> Path:
    """Create annotated confusion matrix heatmap.

    Args:
        cm: Confusion matrix array.
        labels: Class labels.
        filename: Output filename.
        figsize: Figure dimensions.

    Returns:
        Path to saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    labels = labels or ["Low Risk", "High Risk"]

    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
        linewidths=0.5,
        linecolor="white",
        annot_kws={"size": 14},
    )
    ax.set_xlabel("Predicted", fontweight="bold")
    ax.set_ylabel("Actual", fontweight="bold")
    ax.set_title("Confusion Matrix", fontweight="bold")

    dest = FIGURES_DIR / filename
    fig.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved: {dest}")
    return dest


def plot_feature_importance(
    importance_df: pd.DataFrame,
    top_n: int = 10,
    filename: str = "fig09_feature_importance.png",
    figsize: tuple[float, float] = (8, 6),
) -> Path:
    """Create horizontal bar chart of feature importance.

    Args:
        importance_df: DataFrame with 'feature' and 'importance' columns.
        top_n: Number of top features to show.
        filename: Output filename.
        figsize: Figure dimensions.

    Returns:
        Path to saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = importance_df.nlargest(top_n, "importance")

    fig, ax = plt.subplots(figsize=figsize)

    bars = ax.barh(
        df["feature"].str.replace("_", " ").str.title(),
        df["importance"],
        color="#4477AA",
        edgecolor="white",
    )

    ax.set_xlabel("Importance (Mean Decrease in Impurity)")
    ax.set_title("Random Forest Feature Importance", fontweight="bold")
    ax.invert_yaxis()

    # Add value labels
    for bar, val in zip(bars, df["importance"]):
        ax.text(
            val + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{val:.3f}", va="center", fontsize=9,
        )

    dest = FIGURES_DIR / filename
    fig.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved: {dest}")
    return dest


def plot_yearly_moran_comparison(
    yearly_df: pd.DataFrame,
    filename: str = "fig04_moran_yearly.png",
    figsize: tuple[float, float] = (8, 5),
) -> Path:
    """Plot Moran's I values across years for sensitivity analysis.

    Args:
        yearly_df: DataFrame with columns: year, I, p_value.
        filename: Output filename.
        figsize: Figure dimensions.

    Returns:
        Path to saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(yearly_df["year"], yearly_df["I"], "o-", color="#4477AA",
            linewidth=2, markersize=8)

    # Annotate with significance
    for _, row in yearly_df.iterrows():
        sig = "***" if row["p_value"] < 0.001 else "**" if row["p_value"] < 0.01 else "*" if row["p_value"] < 0.05 else "ns"
        ax.annotate(
            f"I={row['I']:.3f}{sig}",
            (row["year"], row["I"]),
            textcoords="offset points",
            xytext=(0, 12),
            ha="center",
            fontsize=9,
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("Moran's I")
    ax.set_title("Global Moran's I by Year — Sensitivity Analysis", fontweight="bold")
    ax.set_xticks(yearly_df["year"])
    ax.grid(True, alpha=0.3)

    # Note about 2021
    ax.annotate(
        "2021: post-COVID\nrecovery period",
        xy=(2021, yearly_df.loc[yearly_df["year"] == 2021, "I"].values[0]),
        xytext=(2021.5, yearly_df["I"].max() + 0.01),
        arrowprops=dict(arrowstyle="->", color="grey"),
        fontsize=8,
        color="grey",
        style="italic",
    )

    dest = FIGURES_DIR / filename
    fig.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved: {dest}")
    return dest
