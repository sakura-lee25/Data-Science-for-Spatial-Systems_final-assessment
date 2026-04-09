"""Coordinate reference system conversion utilities."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.utils.config import CRS_OSGB, CRS_WGS84


def df_to_geodf_osgb(
    df: pd.DataFrame,
    x_col: str = "location_easting_osgr",
    y_col: str = "location_northing_osgr",
) -> gpd.GeoDataFrame:
    """Convert a DataFrame with OSGB36 easting/northing to a GeoDataFrame.

    Args:
        df: Input DataFrame with coordinate columns.
        x_col: Column name for easting.
        y_col: Column name for northing.

    Returns:
        GeoDataFrame in EPSG:27700.
    """
    geometry = [
        Point(x, y) if pd.notna(x) and pd.notna(y) else None
        for x, y in zip(df[x_col], df[y_col])
    ]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=CRS_OSGB)
    return gdf


def reproject_to_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Reproject a GeoDataFrame from OSGB36 to WGS84.

    Args:
        gdf: GeoDataFrame in EPSG:27700.

    Returns:
        GeoDataFrame in EPSG:4326.
    """
    return gdf.to_crs(CRS_WGS84)
