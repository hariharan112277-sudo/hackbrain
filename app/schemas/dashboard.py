"""
Dashboard & KPI aggregation schemas.
"""
from typing import Dict, List, Any
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Fleet-wide dashboard summary."""

    total_machines: int
    online_count: int
    offline_count: int
    critical_alarms_count: int


class KPIMetrics(BaseModel):
    """Industrial Digital Twin KPIs."""

    overall_equipment_effectiveness_oee: float
    mean_time_between_failures_mtbf_hours: float
    mean_time_to_repair_mttr_hours: float
