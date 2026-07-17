"""
Industrial IoT Schemas
Phase 5: Machine, telemetry, alarm, and metadata models for Member 2 & 4 integration.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from enum import Enum


class MachineStatus(str, Enum):
    """Machine operational status."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    UNKNOWN = "unknown"


class AlarmSeverity(str, Enum):
    """Alarm severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlarmStatus(str, Enum):
    """Alarm lifecycle status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


# Machine Schemas
class MachineBase(BaseModel):
    """Base machine fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Machine name")
    serial_number: str = Field(..., min_length=1, max_length=100, description="Serial number")
    model: Optional[str] = Field(default=None, max_length=100, description="Machine model")
    manufacturer: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=255)
    status: MachineStatus = Field(default=MachineStatus.UNKNOWN)
    parent_id: Optional[UUID] = Field(default=None, description="Parent machine ID")
    tags: Dict[str, str] = Field(default={}, description="Custom tags")


class MachineCreate(MachineBase):
    """Machine creation request."""
    pass


class MachineUpdate(BaseModel):
    """Machine update request."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    serial_number: Optional[str] = Field(default=None, min_length=1, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    manufacturer: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=255)
    status: Optional[MachineStatus] = Field(default=None)
    parent_id: Optional[UUID] = Field(default=None)
    tags: Optional[Dict[str, str]] = Field(default=None)


class MachineResponse(MachineBase):
    """Machine response model."""
    id: UUID = Field(..., description="Unique machine identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_telemetry_at: Optional[datetime] = Field(default=None, description="Last telemetry timestamp")

    class Config:
        from_attributes = True


class MachineListResponse(BaseModel):
    """Paginated machine list response."""
    machines: List[MachineResponse] = Field(..., description="List of machines")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages")


# Telemetry Schemas
class TelemetryMetric(BaseModel):
    """Individual telemetry metric with mapping-style read compatibility."""
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    timestamp: Optional[datetime] = Field(default=None, description="Reading timestamp")
    quality: Optional[str] = Field(default="good", description="Data quality")

    def __getitem__(self, key: str) -> Any:
        """Support existing consumers that read metric fields as a mapping."""
        return getattr(self, key)


class TelemetryResponse(BaseModel):
    """Telemetry data response."""
    machine_id: UUID = Field(..., description="Machine identifier")
    metrics: List[TelemetryMetric] = Field(..., description="Metric readings")
    timestamp: datetime = Field(..., description="Data timestamp")


class TelemetryHistoryRequest(BaseModel):
    """Telemetry history query parameters."""
    machine_id: UUID = Field(..., description="Machine identifier")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    metrics: Optional[List[str]] = Field(default=None, description="Specific metrics to retrieve")
    aggregation: Optional[str] = Field(default=None, description="Aggregation function (avg, min, max, sum)")
    interval: Optional[str] = Field(default=None, description="Aggregation interval (1m, 5m, 1h, 1d)")
    limit: int = Field(default=1000, ge=1, le=10000, description="Maximum records")


class TelemetryStatisticsResponse(BaseModel):
    """Telemetry statistics response."""
    machine_id: UUID = Field(..., description="Machine identifier")
    metric: str = Field(..., description="Metric name")
    count: int = Field(..., description="Number of samples")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    avg: float = Field(..., description="Average value")
    std: float = Field(..., description="Standard deviation")
    start_time: datetime = Field(..., description="Period start")
    end_time: datetime = Field(..., description="Period end")


# Alarm Schemas
class AlarmBase(BaseModel):
    """Base alarm fields."""
    machine_id: UUID = Field(..., description="Machine identifier")
    alarm_code: str = Field(..., min_length=1, max_length=50, description="Alarm code")
    message: str = Field(..., min_length=1, max_length=500, description="Alarm message")
    severity: AlarmSeverity = Field(..., description="Alarm severity")
    source: Optional[str] = Field(default=None, max_length=100, description="Alarm source")


class AlarmResponse(AlarmBase):
    """Alarm response model."""
    id: UUID = Field(..., description="Unique alarm identifier")
    status: AlarmStatus = Field(..., description="Alarm status")
    acknowledged_by: Optional[UUID] = Field(default=None, description="Acknowledging user")
    acknowledged_at: Optional[datetime] = Field(default=None, description="Acknowledgment timestamp")
    resolved_by: Optional[UUID] = Field(default=None, description="Resolving user")
    resolved_at: Optional[datetime] = Field(default=None, description="Resolution timestamp")
    resolution_notes: Optional[str] = Field(default=None, description="Resolution notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class AlarmAcknowledgeRequest(BaseModel):
    """Alarm acknowledgment request."""
    notes: Optional[str] = Field(default=None, max_length=1000, description="Acknowledgment notes")


class AlarmResolveRequest(BaseModel):
    """Alarm resolution request."""
    resolution_notes: str = Field(..., min_length=1, max_length=1000, description="Resolution notes")


class AlarmListResponse(BaseModel):
    """Paginated alarm list response."""
    alarms: List[AlarmResponse] = Field(..., description="List of alarms")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages")


class AlarmStatisticsResponse(BaseModel):
    """Alarm statistics for dashboard."""
    total_active: int = Field(..., description="Total active alarms")
    by_severity: Dict[str, int] = Field(..., description="Count by severity")
    by_status: Dict[str, int] = Field(..., description="Count by status")
    by_machine: Dict[str, int] = Field(..., description="Count by machine")
    recent_trend: List[Dict[str, Any]] = Field(..., description="Recent alarm trend")


# Metadata Schemas
class SensorDefinition(BaseModel):
    """Sensor definition."""
    id: str = Field(..., description="Sensor identifier")
    name: str = Field(..., description="Sensor name")
    type: str = Field(..., description="Sensor type")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    location: Optional[str] = Field(default=None, description="Physical location")
    sampling_rate: Optional[float] = Field(default=None, description="Sampling rate (Hz)")
    range_min: Optional[float] = Field(default=None, description="Minimum range")
    range_max: Optional[float] = Field(default=None, description="Maximum range")


class ThresholdConfig(BaseModel):
    """Alarm threshold configuration."""
    metric: str = Field(..., description="Metric name")
    warning_low: Optional[float] = Field(default=None)
    warning_high: Optional[float] = Field(default=None)
    critical_low: Optional[float] = Field(default=None)
    critical_high: Optional[float] = Field(default=None)
    enabled: bool = Field(default=True)


class MachineMetadataResponse(BaseModel):
    """Complete machine metadata response."""
    machine_id: UUID = Field(..., description="Machine identifier")
    sensors: List[SensorDefinition] = Field(..., description="Sensor definitions")
    thresholds: Dict[str, ThresholdConfig] = Field(..., description="Alarm thresholds")
    maintenance_schedule: List[Dict[str, Any]] = Field(..., description="Maintenance schedule")
    firmware_version: Optional[str] = Field(default=None)
    documentation: List[Dict[str, str]] = Field(default=[], description="Documentation links")


# AI Integration Schemas (Member 3 stubs)
class AnomalyPredictionRequest(BaseModel):
    """Anomaly detection request (Member 3 integration)."""
    machine_id: UUID = Field(..., description="Machine identifier")
    telemetry_window: List[TelemetryMetric] = Field(..., description="Recent telemetry window")
    sensitivity: Optional[float] = Field(default=0.95, ge=0.5, le=1.0)


class AnomalyPredictionResponse(BaseModel):
    """Anomaly detection response (Member 3 integration)."""
    machine_id: UUID
    anomaly_detected: bool
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    anomaly_type: Optional[str] = None
    affected_metrics: List[str] = Field(default=[])
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime
    model_version: str


class RULPredictionRequest(BaseModel):
    """Remaining Useful Life prediction request (Member 3 integration)."""
    machine_id: UUID
    telemetry_history: List[TelemetryMetric]
    operating_conditions: Optional[Dict[str, Any]] = None


class RULPredictionResponse(BaseModel):
    """RUL prediction response (Member 3 integration)."""
    machine_id: UUID
    predicted_rul_hours: float
    confidence_interval: Dict[str, float] = Field(..., description="Lower/upper bounds")
    confidence: float = Field(..., ge=0.0, le=1.0)
    degradation_stage: str
    contributing_factors: List[str] = Field(default=[])
    timestamp: datetime
    model_version: str