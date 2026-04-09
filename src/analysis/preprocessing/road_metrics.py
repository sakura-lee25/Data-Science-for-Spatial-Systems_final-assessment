"""Compute road network metrics per MSOA from OS Open Roads."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from loguru import logger
from shapely.geometry import Point

from src.utils.config import CRS_OSGB, RAW_DIR, ensure_file


def compute_road_metrics(
    msoa_path: Path | None = None,
    roads_path: Path | None = None,
) -> pd.DataFrame:
    """Compute road length and junction density per MSOA.

    Metrics:
        - road_length_km: Total road length within the MSOA (km)
        - road_density: road_length_km / area_km2
        - junction_count: Number of road nodes classified as junctions
        - junction_density: junction_count / area_km2

    Args:
        msoa_path: Path to MSOA boundary GeoPackage.
        roads_path: Path to OS Open Roads GeoPackage.

    Returns:
        DataFrame with columns: msoa_code, road_length_km, road_density,
        junction_count, junction_density.
    """
    msoa_path = msoa_path or (RAW_DIR / "msoa_2021_boundaries.gpkg")
    msoa_path = ensure_file(msoa_path)
    roads_path = roads_path or _find_roads_gpkg()

    # Load MSOA boundaries
    logger.info("Loading MSOA boundaries...")
    msoa = gpd.read_file(msoa_path)
    if msoa.crs is None:
        msoa = msoa.set_crs(CRS_OSGB)
    elif msoa.crs.to_epsg() != 27700:
        msoa = msoa.to_crs(CRS_OSGB)

    msoa_code_col = _find_column(msoa.columns, ["MSOA21CD", "msoa21cd"])
    msoa = msoa.rename(columns={msoa_code_col: "msoa_code"})

    # Compute area in km²
    msoa["area_km2"] = msoa.geometry.area / 1e6

    # Load road links
    logger.info("Loading OS Open Roads road links...")
    roads = gpd.read_file(roads_path, layer="road_link")
    if roads.crs is None:
        roads = roads.set_crs(CRS_OSGB)
    elif roads.crs.to_epsg() != 27700:
        roads = roads.to_crs(CRS_OSGB)

    # Road length per link in km
    roads["length_km"] = roads.geometry.length / 1000

    # Spatial join: road links → MSOA
    logger.info("Spatial join: road links to MSOAs...")
    # Use representative point of each road link for assignment
    roads["centroid"] = roads.geometry.centroid
    roads_points = roads.set_geometry("centroid")
    joined_roads = gpd.sjoin(
        roads_points[["length_km", "centroid"]].rename(columns={"centroid": "geometry"}).set_geometry("geometry"),
        msoa[["msoa_code", "geometry"]],
        how="inner",
        predicate="within",
    )

    road_agg = joined_roads.groupby("msoa_code").agg(
        road_length_km=("length_km", "sum"),
    ).reset_index()

    # Load road nodes for junction count
    logger.info("Loading OS Open Roads road nodes...")
    try:
        nodes = gpd.read_file(roads_path, layer="road_node")
        if nodes.crs is None:
            nodes = nodes.set_crs(CRS_OSGB)
        elif nodes.crs.to_epsg() != 27700:
            nodes = nodes.to_crs(CRS_OSGB)

        # Filter to junctions (formOfNode == "junction" or similar)
        form_col = _find_column(
            nodes.columns,
            ["formOfNode", "formofnode", "form_of_node", "formOfRoadNode"],
            required=False,
        )
        if form_col:
            junctions = nodes[nodes[form_col].str.lower().str.contains("junction", na=False)]
        else:
            # If no form column, count all nodes as potential junctions
            junctions = nodes

        logger.info(f"Found {len(junctions):,} junction nodes")

        joined_junctions = gpd.sjoin(
            junctions[["geometry"]],
            msoa[["msoa_code", "geometry"]],
            how="inner",
            predicate="within",
        )
        junction_agg = joined_junctions.groupby("msoa_code").agg(
            junction_count=("index_right", "count"),
        ).reset_index()
    except Exception as e:
        logger.warning(f"Could not load road nodes: {e}. Setting junction_count=0.")
        junction_agg = pd.DataFrame({"msoa_code": msoa["msoa_code"], "junction_count": 0})

    # Merge road and junction metrics
    result = msoa[["msoa_code", "area_km2"]].merge(road_agg, on="msoa_code", how="left")
    result = result.merge(junction_agg, on="msoa_code", how="left")

    result["road_length_km"] = result["road_length_km"].fillna(0)
    result["junction_count"] = result["junction_count"].fillna(0).astype(int)
    result["road_density"] = result["road_length_km"] / result["area_km2"]
    result["junction_density"] = result["junction_count"] / result["area_km2"]

    result = result[
        ["msoa_code", "area_km2", "road_length_km", "road_density", "junction_count", "junction_density"]
    ]

    logger.success(f"Road metrics computed for {len(result):,} MSOAs")
    return result


def _find_roads_gpkg() -> Path:
    """Find the OS Open Roads GeoPackage in the raw data directory."""
    patterns = ["*open-roads*.gpkg", "*OpenRoads*.gpkg", "*roads*.gpkg", "*oproad*.gpkg"]
    candidates = []
    for pat in patterns:
        candidates.extend(RAW_DIR.glob(pat))
        candidates.extend(RAW_DIR.rglob(pat))  # Also search subdirectories
    # Deduplicate
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        raise FileNotFoundError(
            f"No OS Open Roads GeoPackage found in {RAW_DIR}. "
            "Run the scraper first: python -m src.scraper.os_roads"
        )
    return candidates[0]


def _find_column(
    columns: pd.Index,
    candidates: list[str],
    required: bool = True,
) -> str | None:
    """Find the first matching column name from candidates."""
    for c in candidates:
        if c in columns:
            return c
    if required:
        raise KeyError(f"None of {candidates} found in columns: {list(columns)}")
    return None
