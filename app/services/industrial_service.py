"""
Industrial business service.

Orchestrates the Member 2 repository contracts (machines, telemetry, alarms,
metadata). All repository access is performed through the abstract interfaces
defined in app.repositories.interfaces.
"""
from typing import List, Dict, Any, Optional

from app.repositories.interfaces import (
    IMachineRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IMetadataRepository,
)
from app.core.exceptions import ResourceNotFoundError


class IndustrialService:
    """Service facade for industrial data operations."""

    def __init__(
        self,
        machine_repo: IMachineRepository,
        telemetry_repo: ITelemetryRepository,
        alarm_repo: IAlarmRepository,
        metadata_repo: IMetadataRepository,
    ):
        self.machine_repo = machine_repo
        self.telemetry_repo = telemetry_repo
        self.alarm_repo = alarm_repo
        self.metadata_repo = metadata_repo

    async def get_all_machines(self) -> List[Dict[str, Any]]:
        """Return all registered machines."""
        return await self.machine_repo.list_machines()

    async def get_machine_details(self, machine_id: str) -> Dict[str, Any]:
        """Return machine details enriched with metadata."""
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine:
            raise ResourceNotFoundError("Machine", machine_id)

        # Aggregate with metadata
        metadata = await self.metadata_repo.get_machine_metadata(machine_id)
        machine["metadata"] = metadata
        return machine

    async def get_latest_telemetry(self, machine_id: str) -> Dict[str, Any]:
        """Return the latest telemetry snapshot for a machine."""
        telemetry = await self.telemetry_repo.get_latest_telemetry(machine_id)
        if not telemetry:
            raise ResourceNotFoundError("Telemetry Data for Machine", machine_id)
        return telemetry

    async def get_active_alarms(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return active alarms, optionally filtered by severity."""
        return await self.alarm_repo.get_active_alarms(severity)
