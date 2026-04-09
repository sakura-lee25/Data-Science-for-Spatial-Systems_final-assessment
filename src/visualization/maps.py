"""Choropleth and spatial maps for academic publication."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from loguru import logger
from matplotlib.patches import Patch

from src.utils.config import CRS_OSGB, FIGURE_DPI, FIGURES_DIR


# Academic style defaults
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

# LISA cluster colour scheme
LISA_COLORS = {
    "HH": "#d7191c",
    "LL": "#2c7bb6",
    "HL": "#fdae61",
    "LH": "#abd9e9",
    "NS": "#d3d3d3",
}


def plot_choropleth(
    gdf: gpd.GeoDataFrame,
    column: str = "accident_rate_per_10k",
    title: str = "Accident Rate per 10,000 Population",
    cmap: str = "YlOrRd",
    filename: str = "fig01_accident_rate_choropleth.png",
    figsize: tuple[float, float] = (10, 12),
) -> Path:
    """Create a choropleth map of an MSOA-level variable.

    Args:
        gdf: GeoDataFrame with geometry and the target column.
        column: Column to visualise.
        title: Map title.
        cmap: Matplotlib colourmap.
        filename: Output filename.
        figsize: Figure dimensions.

    Returns:
        Path to saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    gdf.plot(
        column=column,
        cmap=cmap,
        legend=True,
        legend_kwds={
            "label": column.replace("_", " ").title(),
            "orientation": "horizontal",
            "shrink": 0.6,
            "pad": 0.02,
        },
        ax=ax,
        edgecolor="face",
        linewidth=0.1,
    )
    ax.set_title(title, fontweight="bold")
    ax.axis("off")

    dest = FIGURES_DIR / filename
    fig.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved: {dest}")
    return dest


def plot_lisa_clusters(
    gdf: gpd.GeoDataFrame,
    cluster_col: str = "lisa_cluster",
    title: str = "LISA Cluster Map — Accident Rate",
    filename: str = "fig03_lisa_clusters.png",
    figsize: tuple[float, float] = (10, 12),
) -> Path:
    """Create a LISA cluster map (HH, LL, HL, LH, NS).

    Args:
        gdf: GeoDataFrame with LISA cluster labels.
        cluster_col: Column with cluster labels.
        title: Map title.
        filename: Output filename.
        figsize: Figure dimensions.

    Returns:
        Path to saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    for cluster, colour in LISA_COLORS.items():
        subset = gdf[gdf[cluster_col] == cluster]
        if not subset.empty:
            subset.plot(ax=ax, color=colour, edgecolor="face", linewidth=0.1)

    legend_elements = [
        Patch(facecolor=c, label=f"{k} ({(gdf[cluster_col] == k).sum():,})")
        for k, c in LISA_COLORS.items()
        if (gdf[cluster_col] == k).sum() > 0
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=9, frameon=True)
    ax.set_title(title, fontweight="bold")
    ax.axis("off")

    dest = FIGURES_DIR / filename
    fig.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved: {dest}")
    return dest


def plot_lisa_yearly_comparison(
    yearly_lisa: dict[int, gpd.GeoDataFrame],
    cluster_col: str = "lisa_cluster",
    filename: str = "fig03b_lisa_yearly_comparison.png",
    figsize: tuple[float, float] = (16, 16),
) -> Path:
    """Create a 2x2 panel comparing LISA clusters across years.

    Args:
        yearly_lisa: Dict mapping year → LISA GeoDataFrame.
        cluster_col: Column with cluster labels.
        filename: Output filename.
        figsize: Figure dimensions.

    Returns:
        Path to saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    years = sorted(yearly_lisa.keys())
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes_flat = axes.flatten()

    for i, year in enumerate(years[:4]):
        ax = axes_flat[i]
        gdf = yearly_lisa[year]
        for cluster, colour in LISA_COLORS.items():
            subset = gdf[gdf[cluster_col] == cluster]
            if not subset.empty:
                subset.plot(ax=ax, color=colour, edgecolor="face", linewidth=0.1)

        note = " (post-COVID recovery)" if year == 2021 else ""
        ax.set_title(f"{year}{note}", fontweight="bold")
        ax.axis("off")

    # Shared legend
    legend_elements = [
        Patch(facecolor=c, label=k) for k, c in LISA_COLORS.items()
    ]
    fig.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=5,
        fontsize=10,
        frameon=True,
        bbox_to_anchor=(0.5, 0.02),
    )
    fig.suptitle("LISA Cluster Comparison by Year", fontweight="bold", fontsize=14, y=0.98)
    fig.tight_layout(rect=[0, 0.05, 1, 0.96])

    dest = FIGURES_DIR / filename
    fig.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved: {dest}")
    return dest


def plot_mgwr_coefficients(
    coef_gdf: gpd.GeoDataFrame,
    variables: list[str] | None = None,
    filename_prefix: str = "fig05_mgwr_coef",
    figsize: tuple[float, float] = (10, 12),
) -> list[Path]:
    """Create coefficient surface maps for MGWR variables.

    Args:
        coef_gdf: GeoDataFrame with local MGWR coefficients.
        variables: Coefficient columns to plot.
        filename_prefix: Output filename prefix.
        figsize: Figure dimensions per map.

    Returns:
        List of paths to saved figures.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    if variables is None:
        # Exclude intercept and t-value columns
        variables = [c for c in coef_gdf.columns
                     if c not in ("geometry", "msoa_code", "intercept")
                     and "_tval" not in c]

    paths = []
    for var in variables:
        if var not in coef_gdf.columns:
            continue

        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Diverging colourmap centred on zero
        vmax = max(abs(coef_gdf[var].quantile(0.02)), abs(coef_gdf[var].quantile(0.98)))
        coef_gdf.plot(
            column=var,
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
            legend=True,
            legend_kwds={
                "label": f"Local coefficient: {var}",
                "orientation": "horizontal",
                "shrink": 0.6,
                "pad": 0.02,
            },
            ax=ax,
            edgecolor="face",
            linewidth=0.1,
        )
        ax.set_title(
            f"MGWR Coefficient Surface — {var.replace('_', ' ').title()}",
            fontweight="bold",
        )
        ax.axis("off")

        dest = FIGURES_DIR / f"{filename_prefix}_{var}.png"
        fig.savefig(dest)
        plt.close(fig)
        paths.append(dest)
        logger.info(f"Saved: {dest}")

    return paths
