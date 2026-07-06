"""
Structured logger provisioning system for structural telemetry audit trails.
"""

import sys
import logging
from database.config import db_settings


def get_industrial_logger(name: str) -> logging.Logger:
    """Configures and returns a thread-safe standardized infrastructure logger."""
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(db_settings.LOG_LEVEL)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
