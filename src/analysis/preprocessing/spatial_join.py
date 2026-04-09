"""Spatial join: assign each accident to an MSOA and aggregate."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from loguru import logger

from src.utils.config import CRS_OSGB, RAW_DIR
from src.utils.crs import df_to_geodf_osgb


def spatial_join_to_msoa(
    accidents: pd.DataFrame,
    msoa_path: Path | None = None,
) -> gpd.GeoDataFrame:
    """Spatially join accident points to MSOA polygons.

    Args:
        accidents: Cleaned STATS19 DataFrame with easting/northing columns.
        msoa_path: Path to MSOA boundary GeoPackage.

    Returns:
        GeoDataFrame of accidents with MSOA codes attached.
    """
    msoa_path = msoa_path or (RAW_DIR / "msoa_2021_boundaries.gpkg")
    logger.info(f"Loading MSOA boundaries from {msoa_path}")
    msoa = gpd.read_file(msoa_path)

    if msoa.crs is None:
        msoa = msoa.set_crs(CRS_OSGB)
    elif msoa.crs.to_epsg() != 27700:
        msoa = msoa.to_crs(CRS_OSGB)

    # Identify MSOA code column
    msoa_code_col = _find_column(msoa.columns, ["MSOA21CD", "msoa21cd", "msoa_code"])
    msoa_name_col = _find_column(msoa.columns, ["MSOA21NM", "msoa21nm", "msoa_name"])

    logger.info("Converting accidents to GeoDataFrame...")
    accidents_gdf = df_to_geodf_osgb(accidents)
    accidents_gdf = accidents_gdf[accidents_gdf.geometry.notna()]

    logger.info(f"Performing spatial join ({len(accidents_gdf):,} points → {len(msoa):,} polygons)...")
    joined = gpd.sjoin(
        accidents_gdf,
        msoa[[msoa_code_col, msoa_name_col, "geometry"]].rename(
            columns={msoa_code_col: "msoa_code", msoa_name_col: "msoa_name"}
        ),
        how="inner",
        predicate="within",
    )
    joined = joined.drop(columns=["index_right"], errors="ignore")

    logger.success(
        f"Spatial join complete: {len(joined):,} accidents matched to MSOAs "
        f"({len(joined) / len(accidents_gdf) * 100:.1f}% match rate)"
    )
    return joined


def aggregate_to_msoa(
    joined: gpd.GeoDataFrame,
    msoa_path: Path | None = None,
    year_col: str | None = "accident_year",
    by_year: bool = False,
) -> gpd.GeoDataFrame:
    """Aggregate accident-level data to MSOA level.

    Args:
        joined: Spatially joined accident GeoDataFrame.
        msoa_path: Path to MSOA boundaries for geometry.
        year_col: Column containing year. Used when by_year=True.
        by_year: If True, aggregate per year separately.

    Returns:
        MSOA-level GeoDataFrame with aggregated metrics.
    """
    msoa_path = msoa_path or (RAW_DIR / "msoa_2021_boundaries.gpkg")

    group_cols = ["msoa_code", "msoa_name"]
    if by_year and year_col and year_col in joined.columns:
        group_cols.append(year_col)

    agg = joined.groupby(group_cols).agg(
        accident_count=("accident_index", "count"),
        severe_count=("is_severe", "sum"),
        casualty_total=("number_of_casualties", "sum"),
        wet_road_count=("is_wet_road", "sum"),
        dark_count=("is_dark", "sum"),
        urban_count=("is_urban", "sum"),
    ).reset_index()

    # Compute proportions
    agg["severe_pct"] = agg["severe_count"] / agg["accident_count"]
    agg["wet_road_pct"] = agg["wet_road_count"] / agg["accident_count"]
    agg["dark_pct"] = agg["dark_count"] / agg["accident_count"]
    agg["urban_pct"] = agg["urban_count"] / agg["accident_count"]

    # Reattach geometry from boundaries
    msoa = gpd.read_file(msoa_path)
    msoa_code_col = _find_column(msoa.columns, ["MSOA21CD", "msoa21cd", "msoa_code"])
    msoa = msoa.rename(columns={msoa_code_col: "msoa_code"})

    result = msoa[["msoa_code", "geometry"]].merge(agg, on="msoa_code", how="right")
    result = gpd.GeoDataFrame(result, geometry="geometry", crs=CRS_OSGB)

    logger.success(f"MSOA aggregation: {len(result):,} MSOAs with accident data")
    return result


def _find_column(columns: pd.Index, candidates: list[str]) -> str:
    """Find the first matching column name from candidates."""
    for c in candidates:
        if c in columns:
            return c
    raise KeyError(f"None of {candidates} found in columns: {list(columns)}")
