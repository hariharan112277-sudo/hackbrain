"""
Integration-Service Repository Adapters.

Concrete implementations of the Phase 4 repository interfaces that delegate to
the existing Member 2 integration services (integration.services) and SQLAlchemy
repositories (database.repository). These adapters bridge the async API surface
expected by the REST tier with the synchronous, session-based integration layer.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.repositories.interfaces import (
    IMachineRepository,
    ITelemetryRepository,
    IAlarmRepository,
    IMetadataRepository,
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
            }

        return await asyncio.to_thread(self._runner.run, _fetch)

    async def list_machines(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        def _fetch(session):
            dtos = self._service.list_machines(session, skip, limit)
            return [
                {
                    "id": str(dto.id),
                    "name": getattr(dto, "name", "Unnamed"),
                    "type": getattr(dto, "current_mode", "AUTOMATIC"),
                    "status": str(dto.status.value).lower(),
                    "location": getattr(dto, "location", "UNKNOWN"),
                }
                for dto in dtos
            ]

        return await asyncio.to_thread(self._runner.run, _fetch)


class IntegrationTelemetryRepository(ITelemetryRepository):
    """Telemetry provider backed by integration.services.TelemetryIntegrationService."""

    def __init__(self, connection_manager: Any):
        self._runner = _SessionRunner(connection_manager)
        self._service = TelemetryIntegrationService()

    async def get_latest_telemetry(self, machine_id: str) -> Optional[Dict[str, Any]]:
        def _fetch(session):
            dtos = self._service.get_latest_machine_telemetry(session, UUID(machine_id))
            if not dtos:
                return None
            latest = max(dtos, key=lambda d: d.timestamp)
            metrics = {str(d.sensor_id): float(d.measured_value) for d in dtos}
            return {
                "machine_id": str(machine_id),
                "timestamp": latest.timestamp,
                "metrics": metrics,
            }

        return await asyncio.to_thread(self._runner.run, _fetch)

    async def get_historical_telemetry(
        self, machine_id: str, metric: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        def _fetch(session):
            from database.models import Telemetry
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
            from database.models import Alarm
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
            from database.models import Alarm
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
    """Metadata provider backed by integration.services.MetadataIntegrationService."""

    def __init__(self, connection_manager: Any):
        self._runner = _SessionRunner(connection_manager)
        self._service = MetadataIntegrationService()
        self._asset_service = AssetIntegrationService()

    async def get_machine_metadata(self, machine_id: str) -> Dict[str, Any]:
        def _fetch(session):
            meta = self._service.get_entity_metadata(session, "machine", UUID(machine_id))
            machine_dto = MachineRegistryService().get_machine(session, UUID(machine_id))
            return {
                "machine": {"id": str(machine_dto.id), "status": str(machine_dto.status.value)},
                "asset": self._asset_service.get_asset(session, machine_dto.asset_id).model_dump(mode="json"),
                "engineering_units": self._service.get_engineering_units_map(),
                **meta,
            }

        return await asyncio.to_thread(self._runner.run, _fetch)
