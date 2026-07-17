"""Canonical Telemetry Schema — Cross-Track Contract."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TelemetryPayload(BaseModel):
    """Raw telemetry payload from MQTT pipeline."""
    model_config = ConfigDict(from_attributes=True)

    asset_id: UUID = Field(..., description="Target asset identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Metric readings")
    source_topic: str = Field(..., description="MQTT topic source")
    quality: str = Field(default="good", description="Data quality label")


class TelemetryResponse(BaseModel):
    """Processed telemetry response for clients."""
    model_config = ConfigDict(from_attributes=True)

    asset_id: UUID
    timestamp: datetime
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    aggregated: Optional[bool] = False
