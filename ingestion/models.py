"""
Domain Data Models for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: ISA-95 Part 2 Equipment Hierarchy, RFC 8259 JSON structures.
Section 4 Implementation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ISA95HierarchyModel:
    """ISA-95 Part 2 hierarchical equipment identification model helper."""
    enterprise: str = "IOB_ENTERPRISE"
    site: str = "SITE_DEFAULT"
    area: str = "AREA_DEFAULT"
    line: str = "LINE_DEFAULT"
    equipment: str = "EQUIPMENT_DEFAULT"


@dataclass
class SensorMeasurementModel:
    """Normalized engineering measurement model helper."""
    metric_name: str = ""
    raw_value: float = 0.0
    normalized_value: float = 0.0
    raw_unit: str = ""
    normalized_unit: str = ""
    quality: str = "GOOD"


@dataclass
class AssetMetadataModel:
    """Static asset metadata enriched during pipeline execution helper."""
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    asset_type: Optional[str] = None
    rated_capacity: Optional[str] = None
    maintenance_zone: Optional[str] = None


@dataclass(frozen=True)
class StandardizedTelemetryModel:
    """Strongly typed internal model representing validated industrial telemetry."""
    timestamp: str = ""
    asset_id: str = ""
    machine_id: str = ""
    sensor_id: str = ""
    topic: str = ""
    measurement: str = ""
    value: float = 0.0
    unit: str = ""
    quality: str = "GOOD"
    sequence_number: int = 0
    gateway_id: str = ""
    site_id: str = ""
    plant_id: str = ""
    line_id: str = ""
    quality_score: float = 100.0
    pipeline_ingest_time: str = ""
    pipeline_version: str = "v4.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Backwards compatibility attributes
    message_id: str = ""
    iso_timestamp: str = ""
    isa95_hierarchy: Any = None
    measurements: Dict[str, Any] = field(default_factory=dict)
    normalized_value: float = 0.0
    normalized_unit: str = ""


@dataclass
class RawTelemetryMessage:
    """Incoming unparsed message container."""
    topic: str
    payload: Any
    qos: int = 1


# Backwards compatibility alias
TelemetryPayloadModel = StandardizedTelemetryModel
