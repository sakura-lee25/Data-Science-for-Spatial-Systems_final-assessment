"""Build the final MSOA-level analysis GeoDataFrame by merging all features."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from loguru import logger

from src.utils.config import (
    CRS_OSGB,
    MSOA_ANALYSIS_GPKG,
    PROCESSED_DIR,
    RAW_DIR,
    YEARS,
)
from src.analysis.preprocessing.stats19_cleaner import load_and_clean_stats19
from src.analysis.preprocessing.spatial_join import (
    aggregate_to_msoa,
    spatial_join_to_msoa,
)
from src.analysis.preprocessing.imd_aggregator import aggregate_imd_to_msoa
from src.analysis.preprocessing.road_metrics import compute_road_metrics


def build_features(force: bool = False) -> gpd.GeoDataFrame:
    """Build the complete MSOA-level feature dataset.

    Pipeline:
        1. Clean STATS19 data (2021-2024 combined)
        2. Spatial join to MSOAs
        3. Aggregate accidents per MSOA
        4. Merge IMD scores
        5. Merge road network metrics
        6. Merge population data
        7. Compute accident rate
        8. Save to GeoPackage

    Also generates per-year datasets for sensitivity analysis.

    Args:
        force: Rebuild even if output exists.

    Returns:
        Final MSOA-level GeoDataFrame.
    """
    if MSOA_ANALYSIS_GPKG.exists() and not force:
        logger.info(f"Loading existing analysis data from {MSOA_ANALYSIS_GPKG}")
        return gpd.read_file(MSOA_ANALYSIS_GPKG)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


    # Step 1: Clean STATS19
    logger.info("=" * 50)
    logger.info("Step 1/7: Cleaning STATS19 data")
    accidents = load_and_clean_stats19()

    # Step 2: Spatial join
    logger.info("Step 2/7: Spatial join to MSOAs")
    joined = spatial_join_to_msoa(accidents)

    # Step 3: Aggregate — combined 2021-2024
    logger.info("Step 3/7: Aggregating to MSOA level")
    msoa_accidents = aggregate_to_msoa(joined)

    # Step 4: IMD scores
    logger.info("Step 4/7: Merging IMD scores")
    imd = aggregate_imd_to_msoa()
    msoa_merged = msoa_accidents.merge(imd, on="msoa_code", how="left")

    # Step 5: Road metrics
    logger.info("Step 5/7: Computing road network metrics")
    road = compute_road_metrics()
    msoa_merged = msoa_merged.merge(
        road[["msoa_code", "road_length_km", "road_density", "junction_count", "junction_density"]],
        on="msoa_code",
        how="left",
    )

    # Step 6: Population
    logger.info("Step 6/7: Merging population data")
    pop = _load_population()
    msoa_merged = msoa_merged.merge(pop, on="msoa_code", how="left")

    # Step 7: Compute rates and final cleanup
    logger.info("Step 7/7: Computing rates and saving")
    msoa_merged["accident_rate_per_10k"] = (
        msoa_merged["accident_count"] / msoa_merged["population"] * 10_000
    )
    msoa_merged["log_accident_rate"] = np.log1p(msoa_merged["accident_rate_per_10k"])

    # Fill remaining NaN
    numeric_cols = msoa_merged.select_dtypes(include="number").columns
    msoa_merged[numeric_cols] = msoa_merged[numeric_cols].fillna(0)

    # Ensure GeoDataFrame
    result = gpd.GeoDataFrame(msoa_merged, geometry="geometry", crs=CRS_OSGB)

    # Filter to England only (MSOA codes starting with E)
    result = result[result["msoa_code"].str.startswith("E")].copy()

    logger.info(f"Final dataset: {len(result):,} MSOAs, {len(result.columns)} columns")
    result.to_file(MSOA_ANALYSIS_GPKG, driver="GPKG")
    logger.success(f"Saved: {MSOA_ANALYSIS_GPKG}")

    # Generate per-year datasets for sensitivity analysis
    _build_yearly_datasets(joined)

    return result


def _build_yearly_datasets(joined: gpd.GeoDataFrame) -> None:
    """Build per-year MSOA aggregations for sensitivity analysis."""
    logger.info("Building per-year datasets for sensitivity analysis...")

    pop = _load_population()

    for year in YEARS:
        year_data = joined[joined["accident_year"] == year].copy()
        if year_data.empty:
            logger.warning(f"No data for year {year}")
            continue

        msoa_year = aggregate_to_msoa(year_data)
        msoa_year = msoa_year.merge(pop, on="msoa_code", how="left")
        msoa_year["accident_rate_per_10k"] = (
            msoa_year["accident_count"] / msoa_year["population"] * 10_000
        )
        msoa_year["log_accident_rate"] = np.log1p(msoa_year["accident_rate_per_10k"])

        numeric_cols = msoa_year.select_dtypes(include="number").columns
        msoa_year[numeric_cols] = msoa_year[numeric_cols].fillna(0)

        # Filter to England
        msoa_year = msoa_year[msoa_year["msoa_code"].str.startswith("E")].copy()
        msoa_year = gpd.GeoDataFrame(msoa_year, geometry="geometry", crs=CRS_OSGB)

        dest = PROCESSED_DIR / f"msoa_yearly_{year}.gpkg"
        msoa_year.to_file(dest, driver="GPKG")
        logger.info(f"Saved yearly data: {dest} ({len(msoa_year):,} MSOAs)")


def _load_population() -> pd.DataFrame:
    """Load MSOA population estimates."""
    pop_path = RAW_DIR / "msoa_population.csv"
    if not pop_path.exists():
        logger.warning("Population data not found — using placeholder zeros")
        return pd.DataFrame(columns=["msoa_code", "population"])

    pop = pd.read_csv(pop_path)

    # Handle Nomis API column naming
    code_col = [c for c in pop.columns if "geography_code" in c.lower() or "code" in c.lower()]
    val_col = [c for c in pop.columns if "obs_value" in c.lower() or "value" in c.lower()]

    if code_col and val_col:
        pop = pop.rename(columns={code_col[0]: "msoa_code", val_col[0]: "population"})
    else:
        # Fall back to first two columns
        pop.columns = ["msoa_code", "population"]

    pop = pop[["msoa_code", "population"]].copy()
    pop["population"] = pd.to_numeric(pop["population"], errors="coerce")
    pop = pop.dropna(subset=["population"])
    logger.info(f"Loaded population data for {len(pop):,} MSOAs")
    return pop


if __name__ == "__main__":
    gdf = build_features(force=True)
    logger.info(f"\nShape: {gdf.shape}")
    logger.info(f"\nColumns: {list(gdf.columns)}")
    logger.info(f"\n{gdf.describe()}")
