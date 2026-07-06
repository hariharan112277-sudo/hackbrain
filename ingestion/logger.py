"""
Structured Logging Module for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: IEC 62443 Security Auditing, RFC 8259 JSON Logging.
"""

import logging
import json
import datetime
from typing import Any, Dict, Optional


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records into JSON strings for downstream aggregation."""
    def format(self, record: logging.LogRecord) -> str:
        log_envelope: Dict[str, Any] = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        if hasattr(record, "context"):
            log_envelope["context"] = record.context  # type: ignore
        return json.dumps(log_envelope)


def initialize_pipeline_logger(name: str = "iob") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(console_handler)
    return logger


# Backwards compatibility helpers
def get_logger(name: str = "iob", level: int = logging.INFO, use_json: bool = False) -> logging.Logger:
    return initialize_pipeline_logger(name)


class AuditLogger:
    """IEC 62443 compliant edge audit logger."""
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def log_security_event(self, event_type: str, details: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self._logger.warning(f"[IEC 62443 Security Event: {event_type}] {details}")

    def log_pipeline_stage(self, stage_name: str, status: str, message_id: Optional[str] = None, duration_ms: float = 0.0) -> None:
        self._logger.debug(f"Stage: {stage_name} | Status: {status} | Duration: {duration_ms:.2f}ms")
