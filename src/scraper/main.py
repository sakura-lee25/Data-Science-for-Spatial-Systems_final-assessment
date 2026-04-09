"""Orchestrate all data downloads for the UK traffic accident project."""

from __future__ import annotations

from loguru import logger

from src.utils.config import ensure_dirs
from src.scraper.stats19 import download_stats19
from src.scraper.boundaries import download_msoa_boundaries, download_lsoa_msoa_lookup
from src.scraper.imd import download_imd
from src.scraper.os_roads import download_os_roads
from src.scraper.population import download_population


def main(force: bool = False) -> None:
    """Run all data downloads sequentially.

    Args:
        force: Re-download even if files exist.
    """
    ensure_dirs()
    logger.info("=" * 60)
    logger.info("Starting data collection pipeline")
    logger.info("=" * 60)

    # 1. STATS19 collision data (2021-2024)
    logger.info("[1/5] STATS19 collision data")
    download_stats19(force=force)

    # 2. MSOA boundaries + LSOA-MSOA lookup
    logger.info("[2/5] MSOA boundaries and lookup tables")
    download_msoa_boundaries(force=force)
    download_lsoa_msoa_lookup(force=force)

    # 3. IMD deprivation data
    logger.info("[3/5] IMD 2019 deprivation scores")
    download_imd(force=force)

    # 4. OS Open Roads
    logger.info("[4/5] OS Open Roads network")
    download_os_roads(force=force)

    # 5. Population estimates
    logger.info("[5/5] MSOA population estimates")
    download_population(force=force)

    logger.success("=" * 60)
    logger.success("All data downloads complete!")
    logger.success("=" * 60)


if __name__ == "__main__":
    main()
