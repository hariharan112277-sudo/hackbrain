"""
Dashboard aggregation service.

Builds dashboard summaries and KPIs by composing the machine and alarm
repository contracts. No direct database access is performed here.
"""
from app.repositories.interfaces import IMachineRepository, IAlarmRepository


class DashboardService:
    """Service facade for dashboard KPIs and summaries."""

    def __init__(self, machine_repo: IMachineRepository, alarm_repo: IAlarmRepository):
        self.machine_repo = machine_repo
        self.alarm_repo = alarm_repo

    async def compile_dashboard_summary(self) -> dict:
        """Aggregate fleet-wide machine and alarm counts."""
        machines = await self.machine_repo.list_machines()
        alarms = await self.alarm_repo.get_active_alarms()

        online = sum(1 for m in machines if m.get("status") == "online")
        offline = len(machines) - online
        critical_alarms = sum(1 for a in alarms if a.get("severity") == "critical")

        return {
            "total_machines": len(machines),
            "online_count": online,
            "offline_count": offline,
            "critical_alarms_count": critical_alarms,
        }

    async def get_kpis(self) -> dict:
        """
        Derive industrial Digital Twin metric KPIs like OEE, MTTR, and MTBF.
        In a full setup, these are derived from real-time database time-series aggregates.
        """
        return {
            "overall_equipment_effectiveness_oee": 84.6,
            "mean_time_between_failures_mtbf_hours": 320.5,
            "mean_time_to_repair_mttr_hours": 2.1,
        }
