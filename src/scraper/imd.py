"""Download IMD 2019 (Index of Multiple Deprivation) data."""

from __future__ import annotations

from pathlib import Path

import requests
from loguru import logger
from tqdm import tqdm

from src.utils.config import IMD_URL, RAW_DIR


def download_imd(
    output_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """Download IMD 2019 scores CSV from MHCLG.

    Args:
        output_dir: Target directory. Defaults to config.RAW_DIR.
        force: Re-download even if file exists.

    Returns:
        Path to the downloaded CSV file.
    """
    output_dir = output_dir or RAW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "imd_2019_scores.csv"

    if dest.exists() and not force:
        logger.info(f"IMD 2019 already exists: {dest}")
        return dest

    logger.info(f"Downloading IMD 2019 from {IMD_URL}")
    resp = requests.get(IMD_URL, stream=True, timeout=120)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    with open(dest, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc="IMD 2019"
    ) as pbar:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))

    logger.success(f"Saved IMD data: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


if __name__ == "__main__":
    download_imd()
