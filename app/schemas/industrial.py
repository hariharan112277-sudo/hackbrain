"""
Industrial data schemas: machines, telemetry, alarms, metadata.
"""
from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel


class MachineResponse(BaseModel):
    """Machine registry record returned by the API."""

    id: str
    name: str
    type: str
    status: str
    location: str


class TelemetryResponse(BaseModel):
    """Latest telemetry snapshot for a machine."""

    machine_id: str
    timestamp: datetime
    metrics: Dict[str, float]


class HistoricalDataResponse(BaseModel):
    """Historical telemetry response for a machine and metric."""

    machine_id: str
    metric: str
    datapoints: List[Dict[str, Any]]


class AlarmResponse(BaseModel):
    """Alarm record returned by the API."""

    id: str
    machine_id: str
    severity: str
    message: str
    timestamp: datetime
    is_active: bool
