"""Centralised path and constant configuration for the project."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from urllib.request import urlopen

# ── Project root ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Data directories ──────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"

# ── Output directories ────────────────────────────────────────
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

# ── Analysis constants ────────────────────────────────────────
YEARS = [2021, 2022, 2023, 2024]
CRS_OSGB = "EPSG:27700"
CRS_WGS84 = "EPSG:4326"

# ── STATS19 download URLs ────────────────────────────────────
STATS19_URL_TEMPLATE = (
    "https://data.dft.gov.uk/road-accidents-safety-data/"
    "dft-road-casualty-statistics-collision-{year}.csv"
)

# ── IMD data URL ──────────────────────────────────────────────
IMD_URL = (
    "https://assets.publishing.service.gov.uk/media/"
    "5dc407b440f0b6379a7acc8d/"
    "File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_"
    "Population_Denominators_3.csv"
)

# ── ONS boundaries ────────────────────────────────────────────
MSOA_BOUNDARIES_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "MSOA_2021_EW_BSC_V3_RUC/FeatureServer/0/query"
)

# ── LSOA → MSOA lookup ───────────────────────────────────────
LSOA_MSOA_LOOKUP_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "OA_LSOA_MSOA_EW_DEC_2021_LU_v3/FeatureServer/0/query"
)

# ── Population estimates ──────────────────────────────────────
POPULATION_URL = (
    "https://www.nomisweb.co.uk/api/v01/dataset/NM_2010_1.data.csv"
    "?geography=TYPE297&date=latest&gender=0&c_age=200&measures=20100"
    "&select=geography_code,obs_value"
)

# ── OS Open Roads ─────────────────────────────────────────────
OS_ROADS_URL = (
    "https://api.os.uk/downloads/v1/products/OpenRoads/downloads"
    "?area=GB&format=GeoPackage&redirect"
)

# ── Output file names ────────────────────────────────────────
MSOA_ANALYSIS_GPKG = PROCESSED_DIR / "msoa_analysis.gpkg"
MGWR_COEFFICIENTS_GPKG = PROCESSED_DIR / "mgwr_coefficients.gpkg"

# ── GitHub raw data URLs ─────────────────────────────────────
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/sakura-lee25/"
    "Data-Science-for-Spatial-Systems_final-assessment/main/"
)

# ── Figure DPI ────────────────────────────────────────────────
FIGURE_DPI = 300

# ── High-risk threshold (top percentile) ─────────────────────
HIGH_RISK_PERCENTILE = 80


def ensure_file(local_path: Path, repo_relpath: str | None = None) -> Path:
    """Return *local_path* if it exists, otherwise download from GitHub.

    Args:
        local_path: Expected local file path.
        repo_relpath: Path relative to repo root (e.g. "data/raw/imd.csv").
                      If None, inferred from *local_path* relative to PROJECT_ROOT.

    Returns:
        The local path (downloaded if it was missing).
    """
    if local_path.exists():
        return local_path

    if repo_relpath is None:
        try:
            repo_relpath = str(local_path.relative_to(PROJECT_ROOT))
        except ValueError:
            raise FileNotFoundError(
                f"{local_path} not found and cannot infer GitHub path"
            )

    url = GITHUB_RAW_BASE + repo_relpath
    local_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {repo_relpath} from GitHub ...")
    with urlopen(url) as resp, open(local_path, "wb") as f:
        f.write(resp.read())
    print(f"  Saved to {local_path} ({local_path.stat().st_size / 1e6:.1f} MB)")
    return local_path


def ensure_dirs() -> None:
    """Create all required directories and ensure they are writable.

    In containerised environments (e.g. Docker/Podman with bind mounts),
    directories may exist but not be writable by the current user.  This
    function tries to fix permissions where possible.
    """
    import os
    import stat

    for d in (RAW_DIR, PROCESSED_DIR, CACHE_DIR, FIGURES_DIR, TABLES_DIR):
        d.mkdir(parents=True, exist_ok=True)
        # Try to make directory world-writable (needed for Docker mounts)
        try:
            d.chmod(d.stat().st_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        except OSError:
            pass
        # Also fix permissions on existing files inside output dirs
        if d in (FIGURES_DIR, TABLES_DIR, PROCESSED_DIR, CACHE_DIR):
            for f in d.iterdir():
                if f.is_file():
                    try:
                        f.chmod(f.stat().st_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                    except OSError:
                        pass
