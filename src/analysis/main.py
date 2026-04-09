"""Main analysis pipeline orchestrator."""

from __future__ import annotations

from loguru import logger

from src.analysis.preprocessing.feature_builder import build_features
from src.analysis.spatial_autocorr import run_spatial_autocorrelation
from src.analysis.mgwr_analysis import run_mgwr_analysis
from src.analysis.ml_classification import run_ml_classification


def main(skip_mgwr: bool = False) -> None:
    """Run the complete analysis pipeline.

    Args:
        skip_mgwr: Skip MGWR (takes several hours). Useful for testing.
    """
    logger.info("=" * 60)
    logger.info("UK Road Traffic Accident Spatial Analysis Pipeline")
    logger.info("=" * 60)

    # Phase 2: Build features
    logger.info("\n[Phase 2] Building MSOA feature dataset...")
    build_features()

    # Phase 3: Spatial autocorrelation
    logger.info("\n[Phase 3] Spatial autocorrelation analysis...")
    run_spatial_autocorrelation()

    # Phase 4: MGWR
    if not skip_mgwr:
        logger.info("\n[Phase 4] MGWR analysis (this will take hours)...")
        run_mgwr_analysis()
    else:
        logger.warning("[Phase 4] MGWR skipped (use skip_mgwr=False to enable)")

    # Phase 5: ML classification
    logger.info("\n[Phase 5] ML classification...")
    run_ml_classification()

    logger.success("=" * 60)
    logger.success("All analyses complete!")
    logger.success("=" * 60)


if __name__ == "__main__":
    main(skip_mgwr=True)
