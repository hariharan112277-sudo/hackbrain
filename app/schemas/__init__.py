"""
Pydantic Schemas for API Contracts
Phase 5: Strict JSON output structures for Member 4 Frontend integration.
"""

from app.schemas.auth import (
    Token,
    TokenData,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    PasswordChangeRequest,
)
from app.schemas.users import (
    UserResponse,
    UserCreate,
    UserUpdate,
    UserListResponse,
    RoleResponse,
    PermissionResponse,
)
from app.schemas.industrial import (
    MachineResponse,
    MachineCreate,
    MachineUpdate,
    MachineListResponse,
    TelemetryResponse,
    TelemetryHistoryRequest,
    TelemetryStatisticsResponse,
    AlarmResponse,
    AlarmAcknowledgeRequest,
    AlarmResolveRequest,
    AlarmListResponse,
    AlarmStatisticsResponse,
    MachineMetadataResponse,
    SensorDefinition,
    ThresholdConfig,
)
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    MachineStatusSummary,
    TelemetryWidgetData,
    AlarmWidgetData,
    KPIWidgetData,
    TrendWidgetData,
)

__all__ = [
    # Auth
    "Token",
    "TokenData",
    "LoginRequest",
    "RefreshTokenRequest",
    "RegisterRequest",
    "PasswordChangeRequest",
    # Users
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "UserListResponse",
    "RoleResponse",
    "PermissionResponse",
    # Industrial
    "MachineResponse",
    "MachineCreate",
    "MachineUpdate",
    "MachineListResponse",
    "TelemetryResponse",
    "TelemetryHistoryRequest",
    "TelemetryStatisticsResponse",
    "AlarmResponse",
    "AlarmAcknowledgeRequest",
    "AlarmResolveRequest",
    "AlarmListResponse",
    "AlarmStatisticsResponse",
    "MachineMetadataResponse",
    "SensorDefinition",
    "ThresholdConfig",
    # Dashboard
    "DashboardOverviewResponse",
    "MachineStatusSummary",
    "TelemetryWidgetData",
    "AlarmWidgetData",
    "KPIWidgetData",
    "TrendWidgetData",
]