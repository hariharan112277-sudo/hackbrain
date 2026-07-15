"""
Pydantic Schemas for the Frozen Database Contract
Track A (Database Layer) — Stage 1

Request/response DTOs that mirror the SQLAlchemy ORM models in this package
1:1 (same field names, same optionality, same width limits as the frozen
PostgreSQL schema contract). Classes are suffixed with ``Schema`` /
``Create`` / ``Base`` so they never collide with the ORM class names
(``User``, ``Asset``, ...) when imported together.

Mapping guidance:
  - ``*Create``   → insert payloads (server-generated columns omitted).
  - ``*Schema``   → read/response models (``from_attributes=True`` so they
                    serialize directly from ORM instances).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# users
# --------------------------------------------------------------------------- #
class UserBase(BaseModel):
    email: str = Field(..., max_length=120)
    full_name: Optional[str] = Field(default=None, max_length=120)
    role: str = Field(default="viewer", max_length=20)  # admin | engineer | operator | viewer


class UserCreate(UserBase):
    password_hash: str = Field(..., max_length=255)


class UserSchema(UserBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    created_at: Optional[datetime] = None


# --------------------------------------------------------------------------- #
# auth (Stage 2 — Authentication request DTOs)
# --------------------------------------------------------------------------- #
class LoginRequest(BaseModel):
    """POST /api/v1/auth/login body."""
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """POST /api/v1/auth/refresh body."""
    refresh_token: str = Field(..., min_length=1)


# --------------------------------------------------------------------------- #
# assets
# --------------------------------------------------------------------------- #
class AssetBase(BaseModel):
    asset_id: str = Field(..., max_length=20)
    name: str = Field(..., max_length=120)
    plant_id: str = Field(..., max_length=20)
    line_id: str = Field(..., max_length=20)
    machine_id: str = Field(..., max_length=20)
    asset_type: Optional[str] = Field(default=None, max_length=60)
    install_date: Optional[date] = None
    criticality: Optional[str] = Field(default=None, max_length=20)


class AssetCreate(AssetBase):
    pass


class AssetSchema(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: Optional[datetime] = None


# --------------------------------------------------------------------------- #
# sensors
# --------------------------------------------------------------------------- #
class SensorBase(BaseModel):
    sensor_id: str = Field(..., max_length=20)
    asset_id: Optional[str] = Field(default=None, max_length=20)
    metric_name: str = Field(..., max_length=60)
    unit: Optional[str] = Field(default=None, max_length=20)
    min_range: Optional[Decimal] = None
    max_range: Optional[Decimal] = None


class SensorCreate(SensorBase):
    pass


class SensorSchema(SensorBase):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# telemetry
# --------------------------------------------------------------------------- #
class TelemetryBase(BaseModel):
    asset_id: Optional[str] = Field(default=None, max_length=20)
    ts: datetime
    temperature_c: Optional[Decimal] = None
    pressure_bar: Optional[Decimal] = None
    vibration_mm_s: Optional[Decimal] = None
    rpm: Optional[Decimal] = None
    voltage_v: Optional[Decimal] = None
    current_a: Optional[Decimal] = None
    energy_kwh: Optional[Decimal] = None
    status: Optional[str] = Field(default=None, max_length=20)


class TelemetryCreate(TelemetryBase):
    pass


class TelemetrySchema(TelemetryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --------------------------------------------------------------------------- #
# events
# --------------------------------------------------------------------------- #
class EventBase(BaseModel):
    asset_id: Optional[str] = Field(default=None, max_length=20)
    ts: datetime
    event_type: Optional[str] = Field(default=None, max_length=40)
    description: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventSchema(EventBase):
    model_config = ConfigDict(from_attributes=True)

    event_id: int


# --------------------------------------------------------------------------- #
# maintenance_logs
# --------------------------------------------------------------------------- #
class MaintenanceLogBase(BaseModel):
    asset_id: Optional[str] = Field(default=None, max_length=20)
    performed_at: Optional[datetime] = None
    description: Optional[str] = None
    technician: Optional[str] = Field(default=None, max_length=80)


class MaintenanceLogCreate(MaintenanceLogBase):
    pass


class MaintenanceLogSchema(MaintenanceLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --------------------------------------------------------------------------- #
# alarms
# --------------------------------------------------------------------------- #
class AlarmBase(BaseModel):
    alarm_id: str = Field(..., max_length=30)
    asset_id: Optional[str] = Field(default=None, max_length=20)
    severity: Optional[str] = Field(default=None, max_length=20)  # critical | warning | resolved
    code: Optional[str] = Field(default=None, max_length=40)
    message: Optional[str] = None
    value: Optional[Decimal] = None
    threshold: Optional[Decimal] = None
    ts: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlarmCreate(AlarmBase):
    pass


class AlarmSchema(AlarmBase):
    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "UserBase", "UserCreate", "UserSchema",
    "LoginRequest", "RefreshRequest",
    "AssetBase", "AssetCreate", "AssetSchema",
    "SensorBase", "SensorCreate", "SensorSchema",
    "TelemetryBase", "TelemetryCreate", "TelemetrySchema",
    "EventBase", "EventCreate", "EventSchema",
    "MaintenanceLogBase", "MaintenanceLogCreate", "MaintenanceLogSchema",
    "AlarmBase", "AlarmCreate", "AlarmSchema",
]
