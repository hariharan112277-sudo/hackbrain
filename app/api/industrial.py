"""
Industrial data REST controller.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime

from app.schemas.industrial import MachineResponse, TelemetryResponse, AlarmResponse
from app.services.industrial_service import IndustrialService
from app.repositories.interfaces import (
    IMachineRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IMetadataRepository,
)
from app.core.dependencies import get_current_user

router = APIRouter(tags=["Industrial APIs"])


# Core Mock Repositories to satisfy runtime initialization
class MockMachineRepo(IMachineRepository):
    async def get_by_id(self, machine_id: str):
        return {
            "id": machine_id,
            "name": "Cutter-01",
            "type": "CNC",
            "status": "online",
            "location": "Hall A",
        }

    async def list_machines(self, skip=0, limit=100):
        return [
            {"id": "m1", "name": "CNC-01", "type": "CNC", "status": "online", "location": "Hall A"}
        ]


class MockTelemetryRepo(ITelemetryRepository):
    async def get_latest_telemetry(self, machine_id: str):
        return {
            "machine_id": machine_id,
            "timestamp": datetime.now(),
            "metrics": {"temperature": 72.5},
        }

    async def get_historical_telemetry(self, machine_id: str, metric: str, limit=100):
        return []


class MockAlarmRepo(IAlarmRepository):
    async def get_active_alarms(self, severity=None):
        return [
            {
                "id": "a1",
                "machine_id": "m1",
                "severity": "critical",
                "message": "High temp",
                "timestamp": datetime.now(),
                "is_active": True,
            }
        ]

    async def resolve_alarm(self, alarm_id: str, resolved_by: str):
        return True


class MockMetadataRepo(IMetadataRepository):
    async def get_machine_metadata(self, machine_id: str):
        return {"installation_date": "2024-01-10"}


# Dependency Injection wiring of Member 2 Repositories
def get_machine_repo() -> IMachineRepository:
    return MockMachineRepo()


def get_telemetry_repo() -> ITelemetryRepository:
    return MockTelemetryRepo()


def get_alarm_repo() -> IAlarmRepository:
    return MockAlarmRepo()


def get_metadata_repo() -> IMetadataRepository:
    return MockMetadataRepo()


def get_industrial_service(
    m=Depends(get_machine_repo),
    t=Depends(get_telemetry_repo),
    a=Depends(get_alarm_repo),
    md=Depends(get_metadata_repo),
) -> IndustrialService:
    return IndustrialService(m, t, a, md)


@router.get("/machines", response_model=List[MachineResponse])
async def list_machines(
    service: IndustrialService = Depends(get_industrial_service),
    current_user: dict = Depends(get_current_user),
):
    """List registered industrial machines."""
    return await service.get_all_machines()


@router.get("/machines/{machine_id}", response_model=MachineResponse)
async def get_machine(
    machine_id: str,
    service: IndustrialService = Depends(get_industrial_service),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve a single machine by id."""
    machine = await service.get_machine_details(machine_id)
    return MachineResponse(**machine)


@router.get("/machines/{machine_id}/telemetry/latest", response_model=TelemetryResponse)
async def get_latest_telemetry(
    machine_id: str,
    service: IndustrialService = Depends(get_industrial_service),
    current_user: dict = Depends(get_current_user),
):
    """Return the latest telemetry snapshot for a machine."""
    telemetry = await service.get_latest_telemetry(machine_id)
    return TelemetryResponse(**telemetry)


@router.get("/alarms", response_model=List[AlarmResponse])
async def list_alarms(
    severity: Optional[str] = Query(None),
    service: IndustrialService = Depends(get_industrial_service),
    current_user: dict = Depends(get_current_user),
):
    """List active alarms, optionally filtered by severity."""
    return await service.get_active_alarms(severity)
