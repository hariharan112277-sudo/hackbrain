"""Canonical Alert Schema — Cross-Track Contract."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AlertResponse(BaseModel):
    """Full alert response model."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(...)
    machine_id: UUID = Field(...)
    alarm_code: str = Field(...)
    message: str = Field(...)
    severity: str = Field(...)
    status: str = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    acknowledged_by: Optional[UUID] = None
    resolved_by: Optional[UUID] = None


class AlertShallowResponse(BaseModel):
    """Shallow alert response (ID + severity + status only)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(...)
    alarm_code: str = Field(...)
    severity: str = Field(...)
    status: str = Field(...)
