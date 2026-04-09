"""Aggregate IMD 2019 data from LSOA to MSOA level."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from src.utils.config import RAW_DIR


def aggregate_imd_to_msoa(
    imd_path: Path | None = None,
    lookup_path: Path | None = None,
) -> pd.DataFrame:
    """Aggregate IMD 2019 scores from LSOA to MSOA using population-weighted mean.

    The IMD 2019 data is published at LSOA level. We use the LSOA→MSOA
    lookup table to compute population-weighted average IMD scores at MSOA level.

    Args:
        imd_path: Path to IMD CSV file.
        lookup_path: Path to LSOA-MSOA lookup CSV.

    Returns:
        DataFrame with columns: msoa_code, imd_score, imd_rank.
    """
    imd_path = imd_path or (RAW_DIR / "imd_2019_scores.csv")
    lookup_path = lookup_path or (RAW_DIR / "lsoa_msoa_lookup.csv")

    # Read IMD scores (CSV version)
    logger.info(f"Loading IMD data from {imd_path.name}")
    imd_raw = pd.read_csv(imd_path)

    # Find the right columns by partial match
    lsoa_col = [c for c in imd_raw.columns if "LSOA" in c and "code" in c.lower()][0]
    imd_score_col = [c for c in imd_raw.columns if "Index of Multiple Deprivation" in c and "Score" in c][0]
    pop_col = [c for c in imd_raw.columns if "population" in c.lower()][0]

    imd = imd_raw[[lsoa_col, imd_score_col, pop_col]].copy()
    imd.columns = ["lsoa_code_2011", "imd_score", "population"]

    # Read LSOA→MSOA lookup (LSOA 2021 codes)
    logger.info(f"Loading LSOA-MSOA lookup from {lookup_path.name}")
    lookup = pd.read_csv(lookup_path)

    # The IMD uses 2011 LSOA codes, the lookup uses 2021 LSOA codes.
    # For most LSOAs these are identical; where they differ we still
    # get a reasonable approximation via population-weighted means.
    # Rename for consistency
    lookup_cols = lookup.columns.tolist()
    lsoa_col = [c for c in lookup_cols if "LSOA" in c.upper() and "CD" in c.upper()][0]
    msoa_col = [c for c in lookup_cols if "MSOA" in c.upper() and "CD" in c.upper()][0]
    lookup = lookup.rename(columns={lsoa_col: "lsoa_code", msoa_col: "msoa_code"})

    # Try matching on LSOA code (2011 IMD codes ≈ 2021 codes for most)
    merged = imd.merge(
        lookup[["lsoa_code", "msoa_code"]],
        left_on="lsoa_code_2011",
        right_on="lsoa_code",
        how="inner",
    )
    logger.info(f"Matched {len(merged):,} / {len(imd):,} LSOAs to MSOAs")

    # Population-weighted average IMD score per MSOA
    merged["weighted_imd"] = merged["imd_score"] * merged["population"]
    msoa_imd = merged.groupby("msoa_code").agg(
        total_weighted_imd=("weighted_imd", "sum"),
        total_population=("population", "sum"),
        lsoa_count=("lsoa_code", "count"),
    ).reset_index()

    msoa_imd["imd_score"] = msoa_imd["total_weighted_imd"] / msoa_imd["total_population"]

    # Rank: higher score = more deprived = higher rank number
    msoa_imd["imd_rank"] = msoa_imd["imd_score"].rank(ascending=False).astype(int)

    result = msoa_imd[["msoa_code", "imd_score", "imd_rank"]].copy()
    logger.success(f"IMD aggregated to {len(result):,} MSOAs")
    return result


if __name__ == "__main__":
    df = aggregate_imd_to_msoa()
    logger.info(f"\n{df.describe()}")
