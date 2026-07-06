"""
IOB Centralized Structured Pipeline Logging Architecture.
"""
import logging
import sys


def get_pipeline_logger(name: str) -> logging.Logger:
    """Instantiates a standardized pipeline stream handler logger."""
    logger = logging.getLogger(f"iob.data_pipeline.{name}")
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s]: %(message)s'
        ))
        logger.addHandler(handler)
    return logger
