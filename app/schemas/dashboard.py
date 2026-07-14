"""
Dashboard Schemas
Phase 5: Aggregated data models for Member 4 Frontend UI components.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class MachineStatusSummary(BaseModel):
    """Machine status summary for dashboard overview."""
    total: int = Field(..., description="Total machines")
    online: int = Field(..., description="Online machines")
    offline: int = Field(..., description="Offline machines")
    maintenance: int = Field(..., description="Machines in maintenance")
    error: int = Field(..., description="Machines in error state")
    unknown: int = Field(..., description="Machines with unknown status")


class TelemetryWidgetData(BaseModel):
    """Telemetry widget data for real-time charts."""
    machine_id: UUID = Field(..., description="Machine identifier")
    machine_name: str = Field(..., description="Machine display name")
    metric: str = Field(..., description="Metric name")
    unit: Optional[str] = Field(default=None, description="Unit")
    current_value: float = Field(..., description="Current reading")
    previous_value: Optional[float] = Field(default=None, description="Previous reading")
    change_percent: Optional[float] = Field(default=None, description="Percentage change")
    trend: List[Dict[str, Any]] = Field(..., description="Historical trend points")
    threshold_warning: Optional[float] = Field(default=None)
    threshold_critical: Optional[float] = Field(default=None)
    status: str = Field(..., description="Current status (normal/warning/critical)")
    last_update: datetime = Field(..., description="Last data timestamp")


class AlarmWidgetData(BaseModel):
    """Alarm widget data for alarm panel."""
    active_count: int = Field(..., description="Active alarms count")
    critical_count: int = Field(..., description="Critical alarms count")
    recent_alarms: List[Dict[str, Any]] = Field(..., description="Most recent alarms")
    top_machines: List[Dict[str, Any]] = Field(..., description="Machines with most alarms")


class KPIWidgetData(BaseModel):
    """KPI widget data for metric cards."""
    label: str = Field(..., description="KPI label")
    value: float = Field(..., description="Current value")
    unit: Optional[str] = Field(default=None, description="Unit")
    trend: Optional[float] = Field(default=None, description="Trend percentage")
    trend_direction: str = Field(default="neutral", description="up/down/neutral")
    target: Optional[float] = Field(default=None, description="Target value")
    status: str = Field(default="normal", description="normal/warning/critical")
    timestamp: datetime = Field(..., description="Data timestamp")


class TrendWidgetData(BaseModel):
    """Trend widget data for time-series charts."""
    metric: str = Field(..., description="Metric name")
    unit: Optional[str] = Field(default=None)
    data_points: List[Dict[str, Any]] = Field(..., description="Time-series data")
    aggregation: str = Field(..., description="Aggregation method")
    interval: str = Field(..., description="Time interval")
    period_start: datetime = Field(..., description="Period start")
    period_end: datetime = Field(..., description="Period end")


class DashboardOverviewResponse(BaseModel):
    """Complete dashboard overview response."""
    machine_status: MachineStatusSummary = Field(..., description="Machine status summary")
    telemetry_widgets: List[TelemetryWidgetData] = Field(..., description="Telemetry widgets")
    alarm_widget: AlarmWidgetData = Field(..., description="Alarm widget")
    kpi_widgets: List[KPIWidgetData] = Field(..., description="KPI widgets")
    trend_widgets: List[TrendWidgetData] = Field(..., description="Trend widgets")
    generated_at: datetime = Field(..., description="Response generation timestamp")


class DashboardFilterRequest(BaseModel):
    """Dashboard filter parameters."""
    machine_ids: Optional[List[UUID]] = Field(default=None)
    site_ids: Optional[List[str]] = Field(default=None)
    time_range: str = Field(default="24h", description="Time range (1h, 6h, 24h, 7d, 30d)")
    refresh_interval: int = Field(default=30, description="Auto-refresh interval (seconds)")


class RealtimeTelemetrySubscription(BaseModel):
    """WebSocket subscription for real-time telemetry."""
    machine_ids: List[UUID] = Field(..., description="Machines to subscribe to")
    metrics: Optional[List[str]] = Field(default=None, description="Specific metrics")
    include_thresholds: bool = Field(default=True)


class RealtimeTelemetryMessage(BaseModel):
    """Real-time telemetry WebSocket message."""
    type: str = Field(default="telemetry", description="Message type")
    machine_id: UUID
    machine_name: str
    metrics: List[Dict[str, Any]]
    timestamp: datetime