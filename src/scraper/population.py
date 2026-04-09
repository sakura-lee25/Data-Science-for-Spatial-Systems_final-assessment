"""Download MSOA-level population estimates from ONS Nomis."""

from __future__ import annotations

from pathlib import Path

import requests
from loguru import logger

from src.utils.config import POPULATION_URL, RAW_DIR


def download_population(
    output_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """Download mid-year population estimates at MSOA level from Nomis.

    Args:
        output_dir: Target directory. Defaults to config.RAW_DIR.
        force: Re-download even if file exists.

    Returns:
        Path to the downloaded CSV.
    """
    output_dir = output_dir or RAW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "msoa_population.csv"

    if dest.exists() and not force:
        logger.info(f"Population data already exists: {dest}")
        return dest

    logger.info("Downloading MSOA population estimates from Nomis...")
    resp = requests.get(POPULATION_URL, timeout=120)
    resp.raise_for_status()

    dest.write_text(resp.text, encoding="utf-8")
    logger.success(f"Saved population data: {dest}")
    return dest


if __name__ == "__main__":
    download_population()
