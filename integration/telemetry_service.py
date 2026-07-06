"""
Real-time Ingestion Framework Synchronization Layer.
"""
from typing import List, Any
from uuid import UUID
from integration.interfaces import ITelemetryIntegrationService, ITelemetryRepository, IAlarmRepository
from integration.contracts import TelemetryDTO, AlarmDTO
from integration.exceptions import ResourceNotFoundError


class TelemetryIntegrationService(ITelemetryIntegrationService):
    def __init__(self, telemetry_repo: ITelemetryRepository, alarm_repo: IAlarmRepository):
        self._telemetry_repo = telemetry_repo
        self._alarm_repo = alarm_repo

    def get_latest_machine_telemetry(self, session: Any, machine_id: UUID) -> List[TelemetryDTO]:
        records = self._telemetry_repo.find_latest_by_machine(session, machine_id)
        return [TelemetryDTO.model_validate(r) for r in records]

    def get_latest_sensor_telemetry(self, session: Any, sensor_id: UUID) -> TelemetryDTO:
        record = self._telemetry_repo.find_latest_by_sensor(session, sensor_id)
        if not record:
            raise ResourceNotFoundError(f"No recent telemetry captures matched sensor ID '{sensor_id}'.")
        return TelemetryDTO.model_validate(record)

    def get_current_alarm_state(self, session: Any, machine_id: UUID) -> List[AlarmDTO]:
        records = self._alarm_repo.get_active_by_machine(session, machine_id)
        return [AlarmDTO.model_validate(r) for r in records]
