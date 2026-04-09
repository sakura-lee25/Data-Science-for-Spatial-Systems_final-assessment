"""I/O utilities for reading large files efficiently."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd
from loguru import logger


def read_csv_chunked(
    filepath: Path,
    chunksize: int = 100_000,
    usecols: list[str] | None = None,
    dtype: dict | None = None,
) -> pd.DataFrame:
    """Read a large CSV file in chunks and concatenate.

    Args:
        filepath: Path to the CSV file.
        chunksize: Number of rows per chunk.
        usecols: Columns to read. None reads all.
        dtype: Column data types.

    Returns:
        Concatenated DataFrame.
    """
    logger.info(f"Reading {filepath.name} in chunks of {chunksize:,}")
    chunks: list[pd.DataFrame] = []
    for i, chunk in enumerate(
        pd.read_csv(filepath, chunksize=chunksize, usecols=usecols, dtype=dtype)
    ):
        chunks.append(chunk)
        if (i + 1) % 5 == 0:
            logger.debug(f"  Read {(i + 1) * chunksize:,} rows...")

    df = pd.concat(chunks, ignore_index=True)
    logger.info(f"Loaded {len(df):,} rows from {filepath.name}")
    return df
