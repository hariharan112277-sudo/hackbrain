"""
Dashboard Service
Phase 5: Aggregates data for Member 4 Frontend UI components.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

import structlog

from app.services.industrial_service import IndustrialService
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    MachineStatusSummary,
    TelemetryWidgetData,
    AlarmWidgetData,
    KPIWidgetData,
    TrendWidgetData,
    DashboardFilterRequest,
)

logger = structlog.get_logger("app.services.dashboard")


class DashboardService:
    """Aggregates data for dashboard UI components."""

    def __init__(self, industrial_service: IndustrialService):
        self.industrial = industrial_service

    async def get_overview(self, filters: Optional[DashboardFilterRequest] = None) -> DashboardOverviewResponse:
        """Get complete dashboard overview."""
        logger.info("dashboard_overview_requested", filters=filters.model_dump() if filters else None)
        
        # Get machine status summary
        machine_status = await self._get_machine_status_summary(filters)
        
        # Get telemetry widgets (top machines by priority)
        telemetry_widgets = await self._get_telemetry_widgets(filters)
        
        # Get alarm widget
        alarm_widget = await self._get_alarm_widget(filters)
        
        # Get KPI widgets
        kpi_widgets = await self._get_kpi_widgets(filters)
        
        # Get trend widgets
        trend_widgets = await self._get_trend_widgets(filters)
        
        return DashboardOverviewResponse(
            machine_status=machine_status,
            telemetry_widgets=telemetry_widgets,
            alarm_widget=alarm_widget,
            kpi_widgets=kpi_widgets,
            trend_widgets=trend_widgets,
            generated_at=datetime.utcnow(),
        )

    async def _get_machine_status_summary(
        self,
        filters: Optional[DashboardFilterRequest] = None,
    ) -> MachineStatusSummary:
        """Get machine status counts."""
        machines = await self.industrial.get_all_machines(
            filters={"status": "all"} if filters and filters.machine_ids else None,
            limit=1000,
        )
        
        # Filter by machine_ids if provided
        if filters and filters.machine_ids:
            machine_id_set = {str(mid) for mid in filters.machine_ids}
            machines = [m for m in machines if m.get("id") in machine_id_set]
        
        status_counts = {
            "online": 0,
            "offline": 0,
            "maintenance": 0,
            "error": 0,
            "unknown": 0,
        }
        
        for machine in machines:
            status = machine.get("status", "unknown").lower()
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts["unknown"] += 1
        
        return MachineStatusSummary(
            total=len(machines),
            online=status_counts["online"],
            offline=status_counts["offline"],
            maintenance=status_counts["maintenance"],
            error=status_counts["error"],
            unknown=status_counts["unknown"],
        )

    async def _get_telemetry_widgets(
        self,
        filters: Optional[DashboardFilterRequest] = None,
    ) -> List[TelemetryWidgetData]:
        """Get telemetry widget data for key machines."""
        widgets = []
        
        # Get machines to display
        machines = await self.industrial.get_all_machines(limit=20)
        if filters and filters.machine_ids:
            machine_id_set = {str(mid) for mid in filters.machine_ids}
            machines = [m for m in machines if m.get("id") in machine_id_set]
        
        # Key metrics to display
        key_metrics = [
            ("temperature", "°C", 80, 95),
            ("pressure", "bar", 10, 15),
            ("vibration", "mm/s", 5, 10),
            ("power", "kW", 100, 150),
        ]
        
        for machine in machines[:10]:  # Limit to 10 machines
            machine_id = UUID(machine["id"])
            
            # Get latest telemetry
            telemetry = await self.industrial.get_latest_telemetry(machine_id)
            if not telemetry:
                continue
            
            metrics = telemetry.get("metrics", {})
            
            for metric_name, unit, warn_thresh, crit_thresh in key_metrics:
                if metric_name not in metrics:
                    continue
                
                value = metrics[metric_name].get("value", 0)
                
                # Determine status
                if value >= crit_thresh:
                    status = "critical"
                elif value >= warn_thresh:
                    status = "warning"
                else:
                    status = "normal"
                
                # Get trend data (last 24 hours)
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=24)
                
                try:
                    history = await self.industrial.get_telemetry_history(
                        machine_id=machine_id,
                        start_time=start_time,
                        end_time=end_time,
                        metrics=[metric_name],
                        aggregation="avg",
                        interval="1h",
                    )
                    trend_points = [
                        {"timestamp": h["timestamp"], "value": h["metrics"][0]["value"]}
                        for h in history
                        if h.get("metrics")
                    ]
                except Exception:
                    trend_points = []
                
                widgets.append(TelemetryWidgetData(
                    machine_id=machine_id,
                    machine_name=machine.get("name", "Unknown"),
                    metric=metric_name,
                    unit=unit,
                    current_value=value,
                    trend=trend_points,
                    threshold_warning=warn_thresh,
                    threshold_critical=crit_thresh,
                    status=status,
                    last_update=telemetry.get("timestamp", datetime.utcnow()),
                ))
        
        return widgets

    async def _get_alarm_widget(
        self,
        filters: Optional[DashboardFilterRequest] = None,
    ) -> AlarmWidgetData:
        """Get alarm widget data."""
        # Get active alarms
        active_alarms = await self.industrial.get_active_alarms(limit=100)
        
        # Filter by machine_ids if provided
        if filters and filters.machine_ids:
            machine_id_set = {str(mid) for mid in filters.machine_ids}
            active_alarms = [a for a in active_alarms if a.get("machine_id") in machine_id_set]
        
        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for alarm in active_alarms:
            sev = alarm.get("severity", "info").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
        
        # Get recent alarms (last 5)
        recent = sorted(
            active_alarms,
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )[:5]
        
        # Top machines by alarm count
        machine_alarm_counts: Dict[str, int] = {}
        for alarm in active_alarms:
            mid = alarm.get("machine_id", "unknown")
            machine_alarm_counts[mid] = machine_alarm_counts.get(mid, 0) + 1
        
        top_machines = sorted(
            machine_alarm_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        
        return AlarmWidgetData(
            active_count=len(active_alarms),
            critical_count=severity_counts["critical"],
            recent_alarms=recent,
            top_machines=[
                {"machine_id": mid, "alarm_count": count}
                for mid, count in top_machines
            ],
        )

    async def _get_kpi_widgets(
        self,
        filters: Optional[DashboardFilterRequest] = None,
    ) -> List[KPIWidgetData]:
        """Get KPI widget data."""
        widgets = []
        
        # Get machine status summary
        status = await self._get_machine_status_summary(filters)
        
        # Overall equipment effectiveness (OEE) - stub
        widgets.append(KPIWidgetData(
            label="Overall Equipment Effectiveness",
            value=87.5,
            unit="%",
            trend=1.2,
            trend_direction="up",
            target=85.0,
            status="normal",
            timestamp=datetime.utcnow(),
        ))
        
        # Machine availability
        availability = (status.online / status.total * 100) if status.total > 0 else 0
        widgets.append(KPIWidgetData(
            label="Machine Availability",
            value=round(availability, 1),
            unit="%",
            trend=0.5,
            trend_direction="up",
            target=95.0,
            status="normal" if availability >= 90 else "warning",
            timestamp=datetime.utcnow(),
        ))
        
        # Active alarms
        alarm_widget = await self._get_alarm_widget(filters)
        widgets.append(KPIWidgetData(
            label="Active Alarms",
            value=alarm_widget.active_count,
            unit="count",
            trend=-2,
            trend_direction="down",
            target=0,
            status="critical" if alarm_widget.critical_count > 0 else "warning" if alarm_widget.active_count > 10 else "normal",
            timestamp=datetime.utcnow(),
        ))
        
        # Critical alarms
        widgets.append(KPIWidgetData(
            label="Critical Alarms",
            value=alarm_widget.critical_count,
            unit="count",
            trend=0,
            trend_direction="neutral",
            target=0,
            status="critical" if alarm_widget.critical_count > 0 else "normal",
            timestamp=datetime.utcnow(),
        ))
        
        # Mean time to acknowledge (MTTA) - stub
        widgets.append(KPIWidgetData(
            label="Mean Time to Acknowledge",
            value=12.5,
            unit="min",
            trend=-1.5,
            trend_direction="down",
            target=15.0,
            status="normal",
            timestamp=datetime.utcnow(),
        ))
        
        # Mean time to resolve (MTTR) - stub
        widgets.append(KPIWidgetData(
            label="Mean Time to Resolve",
            value=4.2,
            unit="hrs",
            trend=-0.3,
            trend_direction="down",
            target=4.0,
            status="normal",
            timestamp=datetime.utcnow(),
        ))
        
        return widgets

    async def _get_trend_widgets(
        self,
        filters: Optional[DashboardFilterRequest] = None,
    ) -> List[TrendWidgetData]:
        """Get trend widget data."""
        widgets = []
        
        # Get machines
        machines = await self.industrial.get_all_machines(limit=5)
        if filters and filters.machine_ids:
            machine_id_set = {str(mid) for mid in filters.machine_ids}
            machines = [m for m in machines if m.get("id") in machine_id_set]
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        key_metrics = ["temperature", "pressure", "vibration", "power"]
        
        for machine in machines[:3]:
            machine_id = UUID(machine["id"])
            
            for metric in key_metrics:
                try:
                    history = await self.industrial.get_telemetry_history(
                        machine_id=machine_id,
                        start_time=start_time,
                        end_time=end_time,
                        metrics=[metric],
                        aggregation="avg",
                        interval="1h",
                    )
                    
                    data_points = [
                        {
                            "timestamp": h["timestamp"],
                            "value": h["metrics"][0]["value"] if h.get("metrics") else 0,
                        }
                        for h in history
                    ]
                    
                    if data_points:
                        widgets.append(TrendWidgetData(
                            metric=f"{machine.get('name', 'Machine')} - {metric}",
                            unit="°C" if metric == "temperature" else "bar" if metric == "pressure" else "mm/s" if metric == "vibration" else "kW",
                            data_points=data_points,
                            aggregation="avg",
                            interval="1h",
                            period_start=start_time,
                            period_end=end_time,
                        ))
                except Exception as e:
                    logger.warning("trend_data_failed", machine_id=str(machine_id), metric=metric, error=str(e))
        
        return widgets

    async def get_machine_detail_dashboard(self, machine_id: UUID) -> Dict[str, Any]:
        """Get detailed dashboard for a single machine."""
        logger.info("machine_detail_dashboard_requested", machine_id=str(machine_id))
        
        # Get machine info
        machine = await self.industrial.get_machine(machine_id)
        
        # Get telemetry flow
        telemetry = await self.industrial.get_machine_telemetry_flow(machine_id)
        
        # Get active alarms for this machine
        alarms = await self.industrial.get_active_alarms(machine_id=machine_id)
        
        # Get metadata
        metadata = await self.industrial.get_machine_metadata(machine_id)
        sensors = await self.industrial.get_machine_sensors(machine_id)
        thresholds = await self.industrial.get_thresholds(machine_id)
        
        return {
            "machine": machine,
            "telemetry": telemetry,
            "active_alarms": alarms,
            "metadata": metadata,
            "sensors": sensors,
            "thresholds": thresholds,
            "generated_at": datetime.utcnow(),
        }