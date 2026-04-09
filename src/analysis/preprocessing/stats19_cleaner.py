"""Clean and standardise STATS19 collision data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from src.utils.config import RAW_DIR, YEARS
from src.utils.io import read_csv_chunked

# Columns required for the analysis
KEEP_COLS = [
    "accident_index",
    "accident_year",
    "accident_severity",
    "location_easting_osgr",
    "location_northing_osgr",
    "road_type",
    "speed_limit",
    "junction_detail",
    "light_conditions",
    "weather_conditions",
    "road_surface_conditions",
    "urban_or_rural_area",
    "number_of_casualties",
]

# Newer STATS19 CSVs use "collision_*" instead of "accident_*"
_COLUMN_RENAMES = {
    "collision_index": "accident_index",
    "collision_year": "accident_year",
    "collision_severity": "accident_severity",
}


def load_and_clean_stats19(
    years: list[int] | None = None,
    raw_dir: Path | None = None,
) -> pd.DataFrame:
    """Load and clean STATS19 collision data for specified years.

    Steps:
        1. Read CSV files for each year
        2. Keep only required columns
        3. Drop rows with missing coordinates
        4. Standardise column types

    Args:
        years: Years to load. Defaults to config.YEARS.
        raw_dir: Directory containing raw CSVs. Defaults to config.RAW_DIR.

    Returns:
        Cleaned DataFrame with all years combined.
    """
    years = years or YEARS
    raw_dir = raw_dir or RAW_DIR

    frames: list[pd.DataFrame] = []
    for year in years:
        filepath = raw_dir / f"stats19_collision_{year}.csv"
        if not filepath.exists():
            logger.warning(f"Missing file: {filepath}")
            continue

        df = read_csv_chunked(filepath)
        frames.append(df)

    if not frames:
        raise FileNotFoundError("No STATS19 files found. Run data download first.")

    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"Combined {len(combined):,} rows from {len(frames)} years")

    # Normalise column names to lowercase with underscores
    combined.columns = (
        combined.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # Handle newer STATS19 naming convention (collision_* → accident_*)
    combined = combined.rename(columns=_COLUMN_RENAMES)

    # Keep only relevant columns (handle possible name variations)
    available = [c for c in KEEP_COLS if c in combined.columns]
    missing = set(KEEP_COLS) - set(available)
    if missing:
        logger.warning(f"Missing columns (will be ignored): {missing}")
    combined = combined[available].copy()

    # Drop rows without valid coordinates
    n_before = len(combined)
    combined = combined.dropna(
        subset=["location_easting_osgr", "location_northing_osgr"]
    )
    combined = combined[
        (combined["location_easting_osgr"] > 0)
        & (combined["location_northing_osgr"] > 0)
    ]
    logger.info(
        f"Dropped {n_before - len(combined):,} rows with invalid coordinates "
        f"({len(combined):,} remaining)"
    )

# Force all column names to lowercase and remove leading and trailing spaces to prevent case sensitivity errors.
    combined.columns = combined.columns.str.lower().str.strip()
    
    # Derive binary flags for aggregation
    combined["is_severe"] = combined["accident_severity"].isin([1, 2]).astype(int)
    combined["is_wet_road"] = (combined["road_surface_conditions"] != 1).astype(int)
    combined["is_dark"] = combined["light_conditions"].isin([4, 5, 6, 7]).astype(int)
    combined["is_urban"] = (combined["urban_or_rural_area"] == 1).astype(int)

    logger.success(f"Cleaned STATS19 data: {len(combined):,} collisions")
    return combined


if __name__ == "__main__":
    df = load_and_clean_stats19()
    logger.info(f"\n{df.dtypes}")
    logger.info(f"\n{df.head()}")
