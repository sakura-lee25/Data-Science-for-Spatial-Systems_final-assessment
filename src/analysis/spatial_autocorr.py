"""Spatial autocorrelation analysis: Global and Local Moran's I."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
from esda.moran import Moran, Moran_Local
from libpysal.weights import Queen
from loguru import logger

from src.utils.config import (
    CRS_OSGB,
    FIGURES_DIR,
    MSOA_ANALYSIS_GPKG,
    PROCESSED_DIR,
    TABLES_DIR,
    YEARS,
    ensure_file,
)


def build_spatial_weights(gdf: gpd.GeoDataFrame) -> Queen:
    """Build Queen contiguity spatial weights matrix.

    Args:
        gdf: MSOA-level GeoDataFrame.

    Returns:
        Queen contiguity weights (row-standardised).
    """
    logger.info("Building Queen contiguity spatial weights...")
    w = Queen.from_dataframe(gdf, use_index=False, silence_warnings=True)
    w.transform = "r"
    logger.info(
        f"Weights: {w.n} observations, mean neighbours = {w.mean_neighbors:.1f}, "
        f"islands = {len(w.islands)}"
    )
    return w


def global_morans_i(
    gdf: gpd.GeoDataFrame,
    variable: str = "accident_rate_per_10k",
    w: Queen | None = None,
    permutations: int = 999,
) -> dict[str, Any]:
    """Compute Global Moran's I for spatial autocorrelation.

    Args:
        gdf: MSOA-level GeoDataFrame.
        variable: Column to test.
        w: Spatial weights. Built from gdf if None.
        permutations: Number of permutations for significance testing.

    Returns:
        Dictionary with Moran's I, expected I, p-value, z-score.
    """
    if w is None:
        w = build_spatial_weights(gdf)

    y = gdf[variable].values
    mi = Moran(y, w, permutations=permutations)

    result = {
        "I": mi.I,
        "expected_I": mi.EI,
        "z_score": mi.z_sim,
        "p_value": mi.p_sim,
        "permutations": permutations,
        "variable": variable,
    }

    logger.info(
        f"Global Moran's I ({variable}): I = {mi.I:.4f}, "
        f"E[I] = {mi.EI:.4f}, z = {mi.z_sim:.4f}, p = {mi.p_sim:.4f}"
    )
    return result


def local_morans_i(
    gdf: gpd.GeoDataFrame,
    variable: str = "accident_rate_per_10k",
    w: Queen | None = None,
    permutations: int = 999,
    significance: float = 0.05,
) -> gpd.GeoDataFrame:
    """Compute Local Moran's I (LISA) and classify clusters.

    Cluster types:
        - HH: High-High (hot spots)
        - LL: Low-Low (cold spots)
        - HL: High-Low (spatial outliers)
        - LH: Low-High (spatial outliers)
        - NS: Not significant

    Args:
        gdf: MSOA-level GeoDataFrame.
        variable: Column to test.
        w: Spatial weights. Built from gdf if None.
        permutations: Number of permutations for significance testing.
        significance: Significance threshold for cluster assignment.

    Returns:
        GeoDataFrame with LISA statistics and cluster labels.
    """
    if w is None:
        w = build_spatial_weights(gdf)

    y = gdf[variable].values
    lisa = Moran_Local(y, w, permutations=permutations)

    result = gdf.copy()
    result["lisa_i"] = lisa.Is
    result["lisa_p"] = lisa.p_sim
    result["lisa_z"] = lisa.z_sim
    result["lisa_q"] = lisa.q  # quadrant: 1=HH, 2=LH, 3=LL, 4=HL

    # Assign cluster labels
    quadrant_labels = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}
    result["lisa_cluster"] = result.apply(
        lambda row: quadrant_labels.get(row["lisa_q"], "NS")
        if row["lisa_p"] < significance
        else "NS",
        axis=1,
    )

    # Summary
    cluster_counts = result["lisa_cluster"].value_counts()
    logger.info(f"LISA cluster summary:\n{cluster_counts.to_string()}")

    return result

ISLAND_CODES = ['E02006781', 'E02006741', 'E02006742', 'E02006752']

def sensitivity_analysis(
    yearly_dir: Path | None = None,
    variable: str = "accident_rate_per_10k",
    permutations: int = 999,
) -> pd.DataFrame:
    """Run Global Moran's I for each year to assess spatial pattern stability.

    Args:
        yearly_dir: Directory containing yearly GeoPackages.
        variable: Variable to test.
        permutations: Number of permutations.

    Returns:
        DataFrame with Moran's I results per year.
    """
    yearly_dir = yearly_dir or PROCESSED_DIR
    results = []

    for year in YEARS:
        filepath = yearly_dir / f"msoa_yearly_{year}.gpkg"
        filepath = ensure_file(filepath)
        if not filepath.exists():
            logger.warning(f"Yearly file not found: {filepath}")
            continue

        gdf = gpd.read_file(filepath)
        gdf = gdf[gdf[variable] > 0].copy()  # Exclude zero-rate MSOAs

        gdf = gdf[~gdf['msoa_code'].isin(ISLAND_CODES)].reset_index(drop=True)

        w = build_spatial_weights(gdf)
        mi_result = global_morans_i(gdf, variable=variable, w=w, permutations=permutations)
        mi_result["year"] = year
        results.append(mi_result)

    df = pd.DataFrame(results)
    logger.info(f"Yearly Moran's I summary:\n{df[['year', 'I', 'p_value']].to_string()}")
    return df


def run_spatial_autocorrelation(
    gpkg_path: Path | None = None,
    variable: str = "accident_rate_per_10k",
) -> tuple[dict, gpd.GeoDataFrame, pd.DataFrame]:
    """Run the complete spatial autocorrelation analysis pipeline.

    Args:
        gpkg_path: Path to MSOA analysis GeoPackage.
        variable: Variable to analyse.

    Returns:
        Tuple of (global_results, lisa_gdf, yearly_sensitivity).
    """
    gpkg_path = gpkg_path or MSOA_ANALYSIS_GPKG
    gpkg_path = ensure_file(gpkg_path)
    logger.info("=" * 50)
    logger.info("Running spatial autocorrelation analysis")
    logger.info("=" * 50)

    # Load data
    gdf = gpd.read_file(gpkg_path)
    gdf = gdf[gdf[variable] > 0].copy()
    logger.info(f"Loaded {len(gdf):,} MSOAs for analysis")

    # Build weights
    w = build_spatial_weights(gdf)

    # Global Moran's I
    global_results = global_morans_i(gdf, variable=variable, w=w)

    # Local Moran's I (LISA)
    lisa_gdf = local_morans_i(gdf, variable=variable, w=w)

    # Save LISA results
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    lisa_summary = lisa_gdf["lisa_cluster"].value_counts().reset_index()
    lisa_summary.columns = ["Cluster", "Count"]
    lisa_summary.to_csv(TABLES_DIR / "lisa_cluster_summary.csv", index=False)

    # Yearly sensitivity
    yearly = sensitivity_analysis(variable=variable)
    yearly.to_csv(TABLES_DIR / "moran_yearly_sensitivity.csv", index=False)

    logger.success("Spatial autocorrelation analysis complete")
    return global_results, lisa_gdf, yearly


if __name__ == "__main__":
    run_spatial_autocorrelation()
