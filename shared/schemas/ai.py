"""Canonical AI Integration Schema — Cross-Track Contract."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AIInferenceRequest(BaseModel):
    """Standard AI inference request payload."""
    model_config = ConfigDict(from_attributes=True)

    model_name: str = Field(default="industrial_default_v2")
    input_vector: Dict[str, Any] = Field(..., description="Feature vector or payload")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    asset_id: Optional[UUID] = None


class AIInferenceResponse(BaseModel):
    """Standard AI inference response payload."""
    model_config = ConfigDict(from_attributes=True)

    request_id: UUID = Field(default_factory=lambda: UUID(int=0))
    result: Dict[str, Any] = Field(default_factory=dict)
    model_version: str = Field(...)
    latency_ms: float = Field(..., ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rate_limit_remaining: int = Field(default=100)
