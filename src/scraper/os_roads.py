"""Download OS Open Roads data from Ordnance Survey Data Hub."""

from __future__ import annotations

import zipfile
from pathlib import Path

import requests
from loguru import logger
from tqdm import tqdm

from src.utils.config import OS_ROADS_URL, RAW_DIR


def download_os_roads(
    output_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """Download OS Open Roads GeoPackage.

    The OS Open Roads dataset is distributed as a zip archive containing
    a GeoPackage file. This function downloads and extracts it.

    Args:
        output_dir: Target directory. Defaults to config.RAW_DIR.
        force: Re-download even if file exists.

    Returns:
        Path to the extracted GeoPackage file.
    """
    output_dir = output_dir or RAW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for already-extracted gpkg (also in subdirectories)
    patterns = ["*open-roads*.gpkg", "*OpenRoads*.gpkg", "*oproad*.gpkg", "*roads*.gpkg"]
    gpkg_candidates = []
    for pat in patterns:
        gpkg_candidates.extend(output_dir.glob(pat))
        gpkg_candidates.extend(output_dir.rglob(pat))
    gpkg_candidates = list(dict.fromkeys(gpkg_candidates))
    if gpkg_candidates and not force:
        logger.info(f"OS Open Roads already exists: {gpkg_candidates[0]}")
        return gpkg_candidates[0]

    zip_dest = output_dir / "os_open_roads.zip"

    if not zip_dest.exists() or force:
        logger.info("Downloading OS Open Roads (this may take several minutes)...")
        resp = requests.get(OS_ROADS_URL, stream=True, timeout=600, allow_redirects=True)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        with open(zip_dest, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc="OS Roads"
        ) as pbar:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
                pbar.update(len(chunk))

        logger.info(f"Downloaded {zip_dest.stat().st_size / 1e6:.1f} MB")

    # Extract GeoPackage from zip
    logger.info("Extracting GeoPackage from archive...")
    with zipfile.ZipFile(zip_dest, "r") as zf:
        gpkg_names = [n for n in zf.namelist() if n.endswith(".gpkg")]
        if not gpkg_names:
            raise FileNotFoundError("No .gpkg file found in the OS Roads zip archive")
        for name in gpkg_names:
            zf.extract(name, output_dir)

    extracted = output_dir / gpkg_names[0]
    logger.success(f"Extracted OS Open Roads: {extracted}")

    # Clean up zip to save space
    zip_dest.unlink()
    logger.info("Removed zip archive to save disk space")

    return extracted


if __name__ == "__main__":
    download_os_roads()
