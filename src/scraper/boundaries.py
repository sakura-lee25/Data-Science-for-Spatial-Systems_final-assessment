"""Download MSOA 2021 boundary data from ONS Open Geography Portal."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import requests
from loguru import logger

from src.utils.config import (
    CRS_OSGB,
    LSOA_MSOA_LOOKUP_URL,
    MSOA_BOUNDARIES_URL,
    RAW_DIR,
)


def _query_arcgis_all(
    base_url: str,
    out_fields: str = "*",
    where: str = "1=1",
    return_geometry: bool = True,
) -> list[dict]:
    """Page through an ArcGIS REST FeatureServer and return all features.

    Args:
        base_url: ArcGIS FeatureServer query endpoint.
        out_fields: Comma-separated field names.
        where: SQL WHERE clause.
        return_geometry: Whether to include geometry in results.

    Returns:
        List of GeoJSON feature dicts.
    """
    all_features: list[dict] = []
    offset = 0
    batch_size = 1000  # ArcGIS default max

    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": batch_size,
            "returnGeometry": str(return_geometry).lower(),
            "outSR": 27700,
        }
        logger.debug(f"Querying offset={offset}")
        resp = requests.get(base_url, params=params, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if not features:
            break
        all_features.extend(features)
        logger.info(f"  Downloaded {len(all_features)} features...")
        offset += len(features)
        if len(features) < batch_size:
            break

    return all_features


def download_msoa_boundaries(
    output_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """Download MSOA 2021 boundaries (England & Wales) as GeoPackage.

    Args:
        output_dir: Target directory. Defaults to config.RAW_DIR.
        force: Re-download even if file exists.

    Returns:
        Path to the downloaded GeoPackage.
    """
    output_dir = output_dir or RAW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "msoa_2021_boundaries.gpkg"

    if dest.exists() and not force:
        logger.info(f"MSOA boundaries already exist: {dest}")
        return dest

    logger.info("Downloading MSOA 2021 boundaries from ONS...")
    features = _query_arcgis_all(MSOA_BOUNDARIES_URL)
    logger.info(f"Retrieved {len(features)} MSOA features")

    geojson = {"type": "FeatureCollection", "features": features}
    gdf = gpd.GeoDataFrame.from_features(geojson, crs=CRS_OSGB)
    gdf.to_file(dest, driver="GPKG")

    logger.success(f"Saved MSOA boundaries: {dest}")
    return dest


def download_lsoa_msoa_lookup(
    output_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """Download LSOA 2021 → MSOA 2021 lookup table.

    Args:
        output_dir: Target directory. Defaults to config.RAW_DIR.
        force: Re-download even if file exists.

    Returns:
        Path to the saved CSV.
    """
    output_dir = output_dir or RAW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "lsoa_msoa_lookup.csv"

    if dest.exists() and not force:
        logger.info(f"LSOA-MSOA lookup already exists: {dest}")
        return dest

    logger.info("Downloading LSOA→MSOA lookup from ONS...")
    features = _query_arcgis_all(
        LSOA_MSOA_LOOKUP_URL,
        out_fields="LSOA21CD,MSOA21CD,MSOA21NM",
        return_geometry=False,
    )
    logger.info(f"Retrieved {len(features)} lookup records")

    # Extract attributes only (no geometry needed)
    import pandas as pd

    rows = [f["properties"] for f in features]
    df = pd.DataFrame(rows)
    # Deduplicate: the OA-LSOA-MSOA lookup may have multiple OA rows per LSOA
    df = df.drop_duplicates(subset=["LSOA21CD"]).reset_index(drop=True)
    logger.info(f"Deduplicated to {len(df)} unique LSOA records")
    df.to_csv(dest, index=False)

    logger.success(f"Saved LSOA-MSOA lookup: {dest}")
    return dest


if __name__ == "__main__":
    download_msoa_boundaries()
    download_lsoa_msoa_lookup()
