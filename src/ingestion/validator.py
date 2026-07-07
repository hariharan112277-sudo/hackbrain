"""
Pydantic-based payload validator for the Stage 1 ingestion boundary.

The wire contract is::

    {
      "device_id":   str,        # min length 3
      "timestamp":   float,      # epoch seconds (UTC)
      "telemetry":   dict[str,float]   # metric_name -> value
    }

Strict Pydantic enforcement is the *first* defense against malformed
or malicious payloads (Risk #1 mitigation: schema-drift guard).
"""
from __future__ import annotations

import logging
from typing import Dict

try:
    from pydantic import BaseModel, Field, ValidationError, ConfigDict
    _PYDANTIC_V2 = True
except ImportError:  # pragma: no cover - v1 fallback
    from pydantic import BaseModel, Field, ValidationError  # type: ignore
    ConfigDict = None  # type: ignore
    _PYDANTIC_V2 = False

logger = logging.getLogger("iob.validator")


class TelemetryPayloadSchema(BaseModel):
    """Strict schema for the Stage 1 telemetry wire contract."""

    device_id: str = Field(..., min_length=3, max_length=128,
                           description="Industrial device identifier")
    timestamp: float = Field(...,
                             description="Epoch timestamp (UTC) from the "
                                         "industrial asset")
    telemetry: Dict[str, float] = Field(..., min_length=1,
                                       description="Metric name -> value")

    if _PYDANTIC_V2 and ConfigDict is not None:
        model_config = ConfigDict(extra="ignore", frozen=False)
    else:
        class Config:
            extra = "ignore"
            frozen = False


class TelemetryValidator:
    """
    Stateless wrapper around the Pydantic schema.

    Raises :class:`pydantic.ValidationError` if the payload is malformed.
    """

    @staticmethod
    def validate_payload(raw_data: dict) -> TelemetryPayloadSchema:
        """Validate a raw JSON payload dict against ``TelemetryPayloadSchema``."""
        try:
            return TelemetryPayloadSchema(**raw_data)
        except ValidationError as exc:
            # Log a clean error message; re-raise for the caller
            logger.warning(f"Payload validation failed: {exc.errors()}")
            raise
