"""Canonical Asset Schema — Cross-Track Contract."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AssetShallowResponse(BaseModel):
    """Shallow asset response with active alert IDs (canonical contract)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique asset identifier")
    name: str = Field(..., max_length=255)
    asset_type: Optional[str] = None
    status: str = Field(..., description="Machine status")
    active_alert_ids: List[UUID] = Field(default_factory=list, description="Active alert UUIDs")


class AssetResponse(AssetShallowResponse):
    """Full asset response."""
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    last_telemetry_at: Optional[datetime] = None
    plant_id: Optional[str] = None
    line_id: Optional[str] = None
    machine_id: Optional[str] = None
