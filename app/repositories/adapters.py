"""
Member 1 - Async Pipeline Integration Adapters (Phase 5 Target).

Implements the repository contracts (IMachineRepository, ITelemetryRepository,
IAlarmRepository, IMetadataRepository, IUserRepository, IRoleRepository,
IPermissionRepository) by wrapping Phase 3/4 integration services and
repositories (database.repository). These adapters bridge the async API surface
with existing synchronous ORM/service implementations via a thread pool executor.
"""

import asyncio
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.repositories.interfaces import (
    IMachineRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IMetadataRepository,
    IUserRepository,
    IRoleRepository,
    IPermissionRepository,
)

# Member 2 integration contracts and services
from integration.services import (
    MachineRegistryService,
    TelemetryIntegrationService,
    MetadataIntegrationService,
    AssetIntegrationService,
)
from integration.mappers import EntityDTOMapper


class _SessionRunner:
    """Helper that opens a SQLAlchemy session, runs a sync callable, and closes it."""

    def __init__(self, connection_manager: Any):
        self._cm = connection_manager

    def run(self, func) -> Any:
        session = self._cm.get_session()
        try:
            return func(session)
        finally:
            session.close()


class IntegrationMachineRepository(IMachineRepository):
    """Machine registry backed by integration.services.MachineRegistryService."""

    def __init__(self, connection_manager: Any):
        self._runner = _SessionRunner(connection_manager)
        self._service = MachineRegistryService()

    async def get_by_id(self, machine_id: str) -> Optional[Dict[str, Any]]:
        def _fetch(session):
            dto = self._service.get_machine(session, UUID(machine_id))
            return {
                "id": str(dto.id),
                "name": getattr(dto, "name", "Unnamed"),
                "type": getattr(dto, "current_mode", "AUTOMATIC"),
                "status": str(dto.status.value).lower(),
                "location": getattr(dto, "location", "UNKNOWN"),
                "created_at": getattr(dto, "created_at", None),
            }

        return await asyncio.to_thread(self._runner.run, _fetch)

    async def list_all(
        self,
        status: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        def _fetch(session):
            dtos = self._service.list_machines(session)
            results = []
            for d in dtos:
                item = {
                    "id": str(d.id),
                    "name": getattr(d, "name", "Unnamed"),
                    "type": getattr(d, "current_mode", "AUTOMATIC"),
                    "status": str(d.status.value).lower(),
                    "location": getattr(d, "location", "UNKNOWN"),
                }
                if status and item["status"] != status.lower():
                    continue
                if type and item["type"] != type:
                    continue
                results.append(item)
            return results[:limit]

        return await asyncio.to_thread(self._runner.run, _fetch)


class IntegrationTelemetryRepository(ITelemetryRepository):
    """Telemetry retrieval backed by the SQLAlchemy Telemetry model."""

    def __init__(self, connection_manager: Any):
        self._runner = _SessionRunner(connection_manager)

    async def get_latest_telemetry(self, machine_id: str) -> Optional[Dict[str, Any]]:
        def _fetch(session):
            from app.models.asset import Telemetry
            r = (
                session.query(Telemetry)
                .filter(Telemetry.machine_id == UUID(machine_id))
                .order_by(Telemetry.timestamp.desc())
                .first()
            )
            if not r:
                return None
            return {
                "machine_id": str(r.machine_id),
                "timestamp": r.timestamp,
                "metrics": {
                    "measured_value": float(r.measured_value),
                },
            }

        return await asyncio.to_thread(self._runner.run, _fetch)

    async def get_historical_telemetry(
        self, machine_id: str, metric: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        def _fetch(session):
            from app.models.asset import Telemetry
            records = (
                session.query(Telemetry)
                .filter(Telemetry.machine_id == UUID(machine_id))
                .order_by(Telemetry.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "timestamp": r.timestamp,
                    "value": float(r.measured_value),
                }
                for r in records
            ]

        return await asyncio.to_thread(self._runner.run, _fetch)


class IntegrationAlarmRepository(IAlarmRepository):
    """Alarm registry backed by the SQLAlchemy Alarm model."""

    def __init__(self, connection_manager: Any):
        self._runner = _SessionRunner(connection_manager)

    async def get_active_alarms(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        def _fetch(session):
            from app.models.alarm import Alarm
            query = session.query(Alarm).filter(Alarm.state != "CLEARED")
            if severity:
                query = query.filter(Alarm.severity == severity.upper())
            alarms = query.all()
            return [
                {
                    "id": str(a.id),
                    "machine_id": str(a.machine_id),
                    "severity": str(a.severity.value).lower(),
                    "message": f"Threshold violated: {a.threshold_violated}",
                    "timestamp": a.trigger_timestamp,
                    "is_active": a.state != "CLEARED",
                }
                for a in alarms
            ]

        return await asyncio.to_thread(self._runner.run, _fetch)

    async def resolve_alarm(self, alarm_id: str, resolved_by: str) -> bool:
        def _resolve(session):
            from app.models.alarm import Alarm
            alarm = session.query(Alarm).filter(Alarm.id == UUID(alarm_id)).first()
            if not alarm:
                return False
            alarm.state = "CLEARED"
            alarm.clear_timestamp = datetime.now(timezone.utc)
            alarm.operator_notes = f"Resolved by {resolved_by}"
            session.commit()
            return True

        return await asyncio.to_thread(self._runner.run, _resolve)


class IntegrationMetadataRepository(IMetadataRepository):
    """Metadata store backed by integration.services.MetadataIntegrationService."""

    def __init__(self, connection_manager: Any):
        self._runner = _SessionRunner(connection_manager)
        self._service = MetadataIntegrationService()

    async def get_metadata(self, entity_id: str) -> Optional[Dict[str, Any]]:
        def _fetch(session):
            return self._service.get_metadata(session, UUID(entity_id))

        return await asyncio.to_thread(self._runner.run, _fetch)
