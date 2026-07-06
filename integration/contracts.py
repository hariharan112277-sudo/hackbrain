"""
Strongly Typed Data Transfer Objects (DTOs) for System Integration.
Implements data validation and serialization strategies via Pydantic v2.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, UUID4, field_validator


class OperationalStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class AlarmSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlarmState(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLEARED = "CLEARED"


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)


# --- Asset Management & Device Topologies DTOs ---

class AssetDTO(BaseDTO):
    id: UUID4
    production_line_id: UUID4
    name: str = Field(..., min_length=2, max_length=100)
    category: str
    manufacturer: str
    model: str
    serial_number: str
    criticality: str
    installation_date: datetime
    commission_date: Optional[datetime] = None
    status: OperationalStatus
    metadata_fields: Dict[str, Any] = Field(default_factory=dict)


class MachineDTO(BaseDTO):
    id: UUID4
    asset_id: UUID4
    gateway_id: UUID4
    firmware_version: str
    operating_hours: float = Field(..., ge=0.0)
    runtime_counter: float = Field(..., ge=0.0)
    current_mode: str
    status: OperationalStatus
    capabilities: List[str] = Field(default_factory=list)
    relationships: Dict[str, UUID4] = Field(default_factory=dict)
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    metadata_fields: Dict[str, Any] = Field(default_factory=dict)


class SensorDTO(BaseDTO):
    id: UUID4
    machine_id: UUID4
    name: str
    sensor_type: str
    measurement_unit: str
    sampling_rate_hz: float = Field(..., gt=0.0)
    calibration_offset: float = 0.0
    lower_threshold: Optional[float] = None
    upper_threshold: Optional[float] = None
    status: OperationalStatus
    metadata_fields: Dict[str, Any] = Field(default_factory=dict)


# --- Telemetry & Analytics Lifecycles DTOs ---

class TelemetryDTO(BaseDTO):
    id: UUID4
    timestamp: datetime
    machine_id: UUID4
    sensor_id: UUID4
    measured_value: float
    quality_code: int = Field(default=192)  # OPC-DA Good Quality = 192
    alarm_status: str = "NORMAL"
    sequence_number: int
    metadata_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("quality_code")
    @classmethod
    def check_industrial_quality_bounds(cls, v: int) -> int:
        if v not in [0, 64, 128, 192]:  # Bad, Uncertain, Good, etc.
            raise ValueError("Invalid industrial OPC quality standard indicator code.")
        return v


class AlarmDTO(BaseDTO):
    id: UUID4
    machine_id: UUID4
    sensor_id: UUID4
    severity: AlarmSeverity
    state: AlarmState
    trigger_timestamp: datetime
    ack_timestamp: Optional[datetime] = None
    clear_timestamp: Optional[datetime] = None
    trigger_value: float
    threshold_violated: str
    operator_notes: Optional[str] = None


class MachineEventDTO(BaseDTO):
    id: UUID4
    machine_id: UUID4
    event_type: str
    timestamp: datetime
    payload: Dict[str, Any] = Field(default_factory=dict)
    operator_id: Optional[UUID4] = None


class MaintenanceLogDTO(BaseDTO):
    id: UUID4
    machine_id: UUID4
    technician_id: UUID4
    maintenance_type: str
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    parts_replaced: List[Dict[str, Any]] = Field(default_factory=list)
    operational_notes: Optional[str] = None
    status: str


# --- Query Filters & Analytics Envelopes DTOs ---

class QueryCriteriaDTO(BaseDTO):
    start_time: datetime
    end_time: datetime
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=5000)
    sort_ascending: bool = Field(default=True)
    filters: Dict[str, Any] = Field(default_factory=dict)


class AggregatedStatisticsDTO(BaseDTO):
    sensor_id: UUID4
    datapoint_count: int
    minimum_value: float
    maximum_value: float
    mean_value: float
    standard_deviation: float
    variance: float
