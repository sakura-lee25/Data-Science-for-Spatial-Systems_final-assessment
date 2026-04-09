"""Download STATS19 collision data from DfT for specified years."""

from __future__ import annotations

from pathlib import Path

import requests
from loguru import logger
from tqdm import tqdm

from src.utils.config import RAW_DIR, STATS19_URL_TEMPLATE, YEARS


def download_stats19(
    years: list[int] | None = None,
    output_dir: Path | None = None,
    force: bool = False,
) -> list[Path]:
    """Download STATS19 collision CSVs for each year.

    Args:
        years: List of years to download. Defaults to config.YEARS.
        output_dir: Target directory. Defaults to config.RAW_DIR.
        force: Re-download even if file exists.

    Returns:
        List of downloaded file paths.
    """
    years = years or YEARS
    output_dir = output_dir or RAW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[Path] = []
    for year in years:
        url = STATS19_URL_TEMPLATE.format(year=year)
        dest = output_dir / f"stats19_collision_{year}.csv"

        if dest.exists() and not force:
            logger.info(f"STATS19 {year} already exists: {dest}")
            downloaded.append(dest)
            continue

        logger.info(f"Downloading STATS19 {year} from {url}")
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=f"STATS19 {year}"
        ) as pbar:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))

        logger.success(f"Saved {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
        downloaded.append(dest)

    return downloaded


if __name__ == "__main__":
    download_stats19()
