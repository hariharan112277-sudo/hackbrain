"""
Structured Logging Module for the Integration Layer.

This module provides backward-compatible logging for the IOB integration layer.
It delegates to the enterprise-grade logging infrastructure in app.core.logging_config
while maintaining the existing get_integration_logger() interface.

Features:
- Structured JSON log output (configurable via AppSettings)
- Correlation ID propagation via ContextVar
- Extra fields support for structured logging

Usage:
    from integration.logger import get_integration_logger

    logger = get_integration_logger()
    logger.info("Service initialized")

    # With structured extra fields:
    logger.info("Machine registered", extra={
        "extra_fields": {"machine_id": "abc-123", "asset_id": "xyz-789"}
    })
"""
import logging
import sys

from app.core.config import settings
from app.core.logging_config import setup_structured_logging, correlation_id_ctx


def get_integration_logger(name: str = "iob.integration") -> logging.Logger:
    """
    Returns a structured logger for the integration layer.

    The logger outputs structured JSON (or plain text in local dev) with
    correlation ID context automatically injected from the request scope.

    Args:
        name: Logger name (defaults to 'iob.integration').

    Returns:
        A configured logging.Logger instance with structured formatting.
    """
    # Ensure structured logging is configured (idempotent)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        setup_structured_logging(
            log_level=settings.LOG_LEVEL,
            json_format=settings.JSON_LOGS,
        )

    logger = logging.getLogger(name)

    # Only add a handler if the logger doesn't already have one
    if not logger.handlers:
        logger.setLevel(settings.LOG_LEVEL)
        handler = logging.StreamHandler(sys.stdout)
        from app.core.logging_config import StructuredJSONFormatter

        handler.setFormatter(StructuredJSONFormatter())
        logger.addHandler(handler)

    return logger
