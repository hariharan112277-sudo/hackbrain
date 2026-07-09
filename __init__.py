"""
Industrial Operating Brain (IOB): Phase 4 — Industrial Telemetry Ingestion Pipeline.
Standard Compliance: ISA-95 Part 2, IEC 62443, ISO/IEC 20922 (MQTT 5.0), RFC 8259 (JSON).
Section 4 Implementation.
"""

from .constants import QUALITY_GOOD, QUALITY_CLAMPED, QUALITY_BAD, QUALITY_UNCERTAIN
from .exceptions import (
    IngestionPipelineException,
    MalformedJsonException,
    SchemaValidationException,
    ClockDriftViolationException,
    DuplicatePacketException,
    UnitConversionException,
    # Aliases
    IngestionException,
    PayloadValidationException,
    TimestampValidationException,
    DuplicatePayloadException,
)
from .logger import StructuredJsonFormatter, initialize_pipeline_logger, get_logger, AuditLogger
from .config import PipelineConfigManager, PipelineConfig
from .models import (
    StandardizedTelemetryModel,
    RawTelemetryMessage,
    TelemetryPayloadModel,
    ISA95HierarchyModel,
    SensorMeasurementModel,
    AssetMetadataModel
)
from .interfaces import IDatabaseWriter, InMemoryDatabaseWriter
from .validator import JsonPayloadValidator
from .timestamp_validator import ChronoTimestampValidator
from .duplicate_detector import SlidingWindowDuplicateDetector
from .quality_checker import OperationalQualityChecker
from .normalizer import EngineeringUnitNormalizer
from .metadata_enricher import StaticAssetMetadataEnricher
from .parser import TelemetryObjectParser
from .retry_manager import ExponentialBackoffRetryManager, RetryManager, retry_on_failure
from .pipeline import TelemetryProcessingPipeline
from .dispatcher import TelemetryEventDispatcher, EventDispatcher
from .subscriber import MqttTelemetrySubscriber

__version__ = "4.0.0-INGEST"
__all__ = [
    "QUALITY_GOOD", "QUALITY_CLAMPED", "QUALITY_BAD", "QUALITY_UNCERTAIN",
    "IngestionPipelineException", "MalformedJsonException", "SchemaValidationException",
    "ClockDriftViolationException", "DuplicatePacketException", "UnitConversionException",
    "StructuredJsonFormatter", "initialize_pipeline_logger", "get_logger", "AuditLogger",
    "PipelineConfigManager", "PipelineConfig",
    "StandardizedTelemetryModel", "RawTelemetryMessage", "TelemetryPayloadModel",
    "ISA95HierarchyModel", "SensorMeasurementModel", "AssetMetadataModel",
    "IDatabaseWriter", "InMemoryDatabaseWriter",
    "JsonPayloadValidator", "ChronoTimestampValidator", "SlidingWindowDuplicateDetector",
    "OperationalQualityChecker", "EngineeringUnitNormalizer", "StaticAssetMetadataEnricher",
    "TelemetryObjectParser", "ExponentialBackoffRetryManager", "RetryManager", "retry_on_failure",
    "TelemetryProcessingPipeline", "TelemetryEventDispatcher", "EventDispatcher",
    "MqttTelemetrySubscriber",
]
