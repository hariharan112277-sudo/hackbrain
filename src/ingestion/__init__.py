"""Ingestion layer — Stage 1.

MQTT subscriber + Pydantic validator + UNS-aware normalization engine.
"""
from .validator import TelemetryPayloadSchema, TelemetryValidator
from .parser import NormalizationEngine
from .mqtt_client import TelemetryIngestionWorker

__all__ = [
    "TelemetryPayloadSchema",
    "TelemetryValidator",
    "NormalizationEngine",
    "TelemetryIngestionWorker",
]
