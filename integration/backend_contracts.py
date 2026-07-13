"""
Phase 2 Backend API Contract Schemas for the Industrial Operating Brain (IOB).

This module is intentionally contract-only:
- no FastAPI routes
- no business rules/workflows
- no direct database operations
- no repository implementation dependencies

It provides frozen Pydantic v2 request/response schemas that can be imported by the
future backend HTTP/WebSocket layer while remaining compatible with the existing
integration.contracts DTO layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


T = TypeVar("T")

EmailIdentity = Annotated[
    str,
    Field(
        min_length=5,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Valid corporate email format identity. Uses regex to avoid optional email-validator runtime dependency.",
    ),
]


class ContractBaseModel(BaseModel):
    """Strict, frozen base model for every external/backend boundary contract."""

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ContractVersion(str, Enum):
    V1 = "v1"


class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class NodeType(str, Enum):
    GATEWAY = "GATEWAY"
    MACHINE = "MACHINE"
    COMPONENT = "COMPONENT"
    SENSOR = "SENSOR"


class TelemetryQuality(str, Enum):
    GOOD = "GOOD"
    UNCERTAIN = "UNCERTAIN"
    BAD = "BAD"


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


class EnterpriseErrorCode(str, Enum):
    ERR_SYS_VAL_01 = "ERR_SYS_VAL_01"
    ERR_SEC_ATH_01 = "ERR_SEC_ATH_01"
    ERR_SEC_AUT_02 = "ERR_SEC_AUT_02"
    ERR_REP_NF_01 = "ERR_REP_NF_01"
    ERR_INF_DB_01 = "ERR_INF_DB_01"
    ERR_SYS_UNK_99 = "ERR_SYS_UNK_99"


class EnterpriseFailureMapping(ContractBaseModel):
    operational_error_context: str
    http_code: int = Field(..., ge=400, le=599)
    error_code: EnterpriseErrorCode
    detail_message_template: str


ENTERPRISE_FAILURE_MAPPING: dict[EnterpriseErrorCode, EnterpriseFailureMapping] = {
    EnterpriseErrorCode.ERR_SYS_VAL_01: EnterpriseFailureMapping(
        operational_error_context="Payload Field Constraint Breach",
        http_code=422,
        error_code=EnterpriseErrorCode.ERR_SYS_VAL_01,
        detail_message_template="Provided field formatting constraints failed validation criteria checks.",
    ),
    EnterpriseErrorCode.ERR_SEC_ATH_01: EnterpriseFailureMapping(
        operational_error_context="Token Missing or Malformed",
        http_code=401,
        error_code=EnterpriseErrorCode.ERR_SEC_ATH_01,
        detail_message_template="Bearer authorization header missing, expired, or cryptographically invalid.",
    ),
    EnterpriseErrorCode.ERR_SEC_AUT_02: EnterpriseFailureMapping(
        operational_error_context="RBAC Authorization Violation",
        http_code=403,
        error_code=EnterpriseErrorCode.ERR_SEC_AUT_02,
        detail_message_template="User identity lacks administrative privileges for target resource node operations.",
    ),
    EnterpriseErrorCode.ERR_REP_NF_01: EnterpriseFailureMapping(
        operational_error_context="Resource Target Missing",
        http_code=404,
        error_code=EnterpriseErrorCode.ERR_REP_NF_01,
        detail_message_template="Requested asset or entity with tracking token identification could not be located.",
    ),
    EnterpriseErrorCode.ERR_INF_DB_01: EnterpriseFailureMapping(
        operational_error_context="Storage Transaction Timeout",
        http_code=503,
        error_code=EnterpriseErrorCode.ERR_INF_DB_01,
        detail_message_template="High-frequency telemetry persistent store failed to respond within strict execution window limits.",
    ),
    EnterpriseErrorCode.ERR_SYS_UNK_99: EnterpriseFailureMapping(
        operational_error_context="Internal Unhandled Fallback",
        http_code=500,
        error_code=EnterpriseErrorCode.ERR_SYS_UNK_99,
        detail_message_template="An unhandled execution state failure occurred within backend core layers.",
    ),
}


class CorrelationContext(ContractBaseModel):
    """Portable representation of mandatory request traceability headers."""

    correlation_id: str = Field(
        ...,
        alias="X-Correlation-ID",
        min_length=16,
        max_length=128,
        pattern=r"^[A-Za-z0-9_.:\-]+$",
    )
    idempotency_key: str | None = Field(
        default=None,
        alias="Idempotency-Key",
        min_length=16,
        max_length=128,
        pattern=r"^[A-Za-z0-9_.:\-]+$",
    )
    actor_id: UUID | None = Field(default=None, description="Authenticated user/service principal UUID")


class TokenObtainRequest(ContractBaseModel):
    username: EmailIdentity
    password: str = Field(..., min_length=12, max_length=128, description="Secured plaintext credential string")
    client_id: str = Field(..., min_length=3, max_length=64)


class TokenRevokeRequest(ContractBaseModel):
    refresh_token: str = Field(..., min_length=32, max_length=4096)
    client_id: str = Field(..., min_length=3, max_length=64)


class TokenResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    access_token: str = Field(..., min_length=32, description="Cryptographically signed JSON Web Token")
    refresh_token: str = Field(..., min_length=32, description="High-entropy opaque lifecycle extension token string")
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = Field(..., gt=0, description="Relative token duration remaining in seconds")


class TimeWindowRequest(ContractBaseModel):
    start_time: datetime = Field(..., description="Inclusive UTC ISO-8601 lower bound")
    end_time: datetime = Field(..., description="Exclusive UTC ISO-8601 upper bound")

    @model_validator(mode="after")
    def validate_window_order(self) -> "TimeWindowRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class PaginationRequest(ContractBaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=5000)
    sort_direction: SortDirection = SortDirection.ASC


class PaginationParams(ContractBaseModel):
    page: int = Field(default=1, ge=1, description="Target page window index")
    limit: int = Field(default=50, ge=1, le=1000, description="Enforced item retrieval limit per window frame")


class TelemetryQueryRequest(TimeWindowRequest):
    machine_id: UUID | None = None
    sensor_id: UUID | None = None
    metric_names: list[str] = Field(default_factory=list, max_length=64)
    quality_filter: list[TelemetryQuality] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=5000)
    sort_direction: SortDirection = SortDirection.ASC

    @model_validator(mode="after")
    def validate_selector(self) -> "TelemetryQueryRequest":
        if self.machine_id is None and self.sensor_id is None:
            raise ValueError("Either machine_id or sensor_id must be supplied")
        return self


class HistoricalQueryRequest(TimeWindowRequest):
    machine_uuid: UUID
    sensor_uuids: list[UUID] = Field(..., min_length=1, max_length=100)
    aggregation_resolution: Literal["1s", "10s", "1m", "5m", "1h"] = "1m"
    pagination: PaginationParams = Field(default_factory=PaginationParams)


class AlarmFilterRequest(ContractBaseModel):
    severity: Literal["INFO", "WARNING", "CRITICAL", "FATAL"] | None = None
    is_acknowledged: bool | None = None
    start_time: datetime | None = None
    pagination: PaginationParams = Field(default_factory=PaginationParams)


class TelemetryStreamRequest(ContractBaseModel):
    machine_ids: list[UUID] = Field(default_factory=list, max_length=100)
    sensor_ids: list[UUID] = Field(default_factory=list, max_length=500)
    topic_filter: str | None = Field(default=None, max_length=256, pattern=r"^[A-Za-z0-9_+/.:\-#]+$")
    min_quality: TelemetryQuality = TelemetryQuality.GOOD

    @model_validator(mode="after")
    def validate_subscription_target(self) -> "TelemetryStreamRequest":
        if not self.machine_ids and not self.sensor_ids and self.topic_filter is None:
            raise ValueError("At least one stream target must be supplied")
        return self


class AssetTreeRequest(ContractBaseModel):
    root_asset_id: UUID
    include_sensors: bool = True
    max_depth: int = Field(default=10, ge=1, le=25)


class AlarmQueryRequest(TimeWindowRequest):
    machine_id: UUID | None = None
    sensor_id: UUID | None = None
    severity: list[AlarmSeverity] = Field(default_factory=list)
    state: list[AlarmState] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=5000)


class AlarmAcknowledgeRequest(ContractBaseModel):
    alarm_id: UUID
    operator_id: UUID
    operator_notes: str | None = Field(default=None, max_length=2000)
    requested_state: Literal["ACKNOWLEDGED"] = "ACKNOWLEDGED"


class AggregationRequest(TimeWindowRequest):
    sensor_id: UUID
    bucket: Literal["1m", "5m", "15m", "1h", "1d"] = "5m"
    functions: list[Literal["min", "max", "mean", "stddev", "variance", "count"]] = Field(
        default_factory=lambda: ["min", "max", "mean", "count"],
        min_length=1,
        max_length=6,
    )


class UpstreamTelemetryMetric(ContractBaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    value: int | float | bool | str
    unit: str | None = Field(default=None, max_length=32)
    quality: TelemetryQuality = TelemetryQuality.GOOD
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpstreamTelemetryPayload(ContractBaseModel):
    timestamp: datetime = Field(..., description="ISO-8601 millisecond precision UTC timestamp")
    edge_node_id: str = Field(..., min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_\-:]+$")
    metrics: list[UpstreamTelemetryMetric] = Field(..., min_length=1, max_length=1000)


class UpstreamAssetNode(ContractBaseModel):
    uuid: UUID
    parent_uuid: UUID | None = None
    node_type: NodeType
    display_name: str = Field(..., min_length=1, max_length=150)
    attributes: dict[str, Any] = Field(default_factory=dict)


class TelemetryPointResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    edge_timestamp: datetime | None = Field(default=None, description="Original timestamp emitted by edge device clock")
    ingest_timestamp: datetime | None = Field(default=None, description="Server UTC timestamp assigned at ingestion boundary")
    machine_id: UUID
    sensor_id: UUID
    metric_name: str = Field(..., min_length=1, max_length=128)
    value: float
    unit: str = Field(..., min_length=1, max_length=32)
    quality: TelemetryQuality
    sequence_number: int = Field(..., ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MachineResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    uuid: UUID = Field(..., description="Global Unique Asset Identifier")
    display_name: str = Field(..., min_length=1, max_length=255)
    model_number: str = Field(..., min_length=1, max_length=128)
    manufacturer: str = Field(..., min_length=1, max_length=128)
    installation_date: str
    operational_status: Literal["ONLINE", "OFFLINE", "MAINTENANCE", "FAULTED"]
    telemetry_metadata: dict[str, Any] = Field(default_factory=dict, description="Dynamic hardware properties structural configuration")


class MetricDataPoint(ContractBaseModel):
    timestamp: datetime
    edge_timestamp: datetime | None = None
    ingest_timestamp: datetime | None = None
    values: dict[str, float | int | str | bool]


class HistoricalQueryResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    machine_uuid: UUID
    data_points: list[MetricDataPoint]
    total_records: int = Field(..., ge=0)
    execution_time_ms: int = Field(..., ge=0)


class SubsystemStatus(ContractBaseModel):
    status: Literal["UP", "DOWN", "DEGRADED"]
    latency_ms: float = Field(..., ge=0.0)


class HealthCheckResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    status: Literal["HEALTHY", "UNHEALTHY"]
    version: str
    environment: str
    dependencies: dict[str, SubsystemStatus]


class MachineSummaryResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    machine_id: UUID
    asset_id: UUID | None = None
    gateway_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=150)
    status: Literal["ONLINE", "OFFLINE", "MAINTENANCE", "DECOMMISSIONED"]
    health_score: float = Field(..., ge=0.0, le=100.0)
    capabilities: list[str] = Field(default_factory=list)


class SensorSummaryResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    sensor_id: UUID
    machine_id: UUID
    name: str = Field(..., min_length=1, max_length=150)
    sensor_type: str = Field(..., min_length=1, max_length=80)
    measurement_unit: str = Field(..., min_length=1, max_length=32)
    sampling_rate_hz: float = Field(..., gt=0.0)
    status: Literal["ONLINE", "OFFLINE", "MAINTENANCE", "DECOMMISSIONED"]


class AlarmResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    alarm_id: UUID
    machine_id: UUID
    sensor_id: UUID | None = None
    severity: AlarmSeverity
    state: AlarmState
    trigger_timestamp: datetime
    ack_timestamp: datetime | None = None
    clear_timestamp: datetime | None = None
    trigger_value: float | None = None
    threshold_violated: str | None = Field(default=None, max_length=128)
    operator_notes: str | None = Field(default=None, max_length=2000)


class AggregatedStatisticsResponse(ContractBaseModel):
    extension_context: dict[str, Any] = Field(default_factory=dict)
    sensor_id: UUID
    bucket_start: datetime
    bucket_end: datetime
    minimum_value: float | None = None
    maximum_value: float | None = None
    mean_value: float | None = None
    standard_deviation: float | None = None
    variance: float | None = None
    datapoint_count: int = Field(..., ge=0)


class ValidationErrorDetails(ContractBaseModel):
    field: str = Field(..., description="Dot-notation pointer to the invalid field payload target location")
    message: str = Field(..., description="Human-readable constraint evaluation failure message context")
    rejected_value: str | None = Field(default=None, description="String representation of the rejected data fragment")


class ProblemDetails(ContractBaseModel):
    type: str = Field(default="about:blank", max_length=512)
    title: str = Field(..., min_length=1, max_length=160)
    status: int = Field(..., ge=400, le=599)
    detail: str = Field(..., min_length=1, max_length=4000)
    instance: str | None = Field(default=None, max_length=512)
    correlation_id: str = Field(..., min_length=16, max_length=128)
    error_code: str = Field(..., min_length=3, max_length=80, pattern=r"^[A-Z0-9_]+$")
    retryable: bool = False
    invalid_params: list[ValidationErrorDetails | dict[str, Any]] = Field(default_factory=list)


# Enterprise naming alias used by the Phase 2 documentation package.
ProblemDetailsResponse = ProblemDetails


class ApiEnvelope(ContractBaseModel, Generic[T]):
    api_version: ContractVersion = ContractVersion.V1
    correlation_id: str = Field(..., min_length=16, max_length=128)
    data: T
    errors: list[ProblemDetails] = Field(default_factory=list)

    @field_validator("errors")
    @classmethod
    def validate_success_error_exclusivity(cls, value: list[ProblemDetails]) -> list[ProblemDetails]:
        return value


class PaginatedResponse(ContractBaseModel, Generic[T]):
    items: list[T]
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=5000)
    total_items: int = Field(..., ge=0)
    has_next: bool
    has_previous: bool
