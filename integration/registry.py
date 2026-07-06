"""
Machine & Sensor Unified Registry Management Services.
"""
from typing import List, Dict, Any
from uuid import UUID
from integration.interfaces import IMachineRegistryService, IMachineRepository, ISensorRegistryService, ISensorRepository
from integration.contracts import MachineDTO, SensorDTO, OperationalStatus
from integration.exceptions import ResourceNotFoundError, DatabaseUnavailableException


class MachineRegistryService(IMachineRegistryService):
    def __init__(self, machine_repo: IMachineRepository):
        self._repo = machine_repo

    def register_machine(self, session: Any, machine_data: Dict[str, Any]) -> MachineDTO:
        try:
            raw_machine = self._repo.save(session, machine_data)
            return MachineDTO.model_validate(raw_machine)
        except Exception as e:
            raise DatabaseUnavailableException("Persistence engine failed to commit registry structural data entry.", {"err": str(e)})

    def get_machine(self, session: Any, machine_id: UUID) -> MachineDTO:
        record = self._repo.find_by_id(session, machine_id)
        if not record:
            raise ResourceNotFoundError(f"Machine reference identifier '{machine_id}' does not exist inside registry databases.")
        return MachineDTO.model_validate(record)

    def list_machines(self, session: Any, skip: int, limit: int) -> List[MachineDTO]:
        records = self._repo.get_all_paginated(session, skip, limit)
        return [MachineDTO.model_validate(r) for r in records]

    def update_machine_metadata(self, session: Any, machine_id: UUID, metadata: Dict[str, Any]) -> MachineDTO:
        record = self._repo.find_by_id(session, machine_id)
        if not record:
            raise ResourceNotFoundError(f"Machine structural reference id '{machine_id}' non-existent.")
        record.metadata_fields.update(metadata)
        updated_record = self._repo.save(session, record)
        return MachineDTO.model_validate(updated_record)

    def lookup_status(self, session: Any, machine_id: UUID) -> OperationalStatus:
        return self.get_machine(session, machine_id).status

    def lookup_capabilities(self, session: Any, machine_id: UUID) -> List[str]:
        return self.get_machine(session, machine_id).capabilities

    def lookup_relationships(self, session: Any, machine_id: UUID) -> Dict[str, UUID]:
        return self.get_machine(session, machine_id).relationships

    def get_health_metric(self, session: Any, machine_id: UUID) -> float:
        return self.get_machine(session, machine_id).health_score


class SensorRegistryService(ISensorRegistryService):
    def __init__(self, sensor_repo: ISensorRepository):
        self._repo = sensor_repo

    def register_sensor(self, session: Any, sensor_data: Dict[str, Any]) -> SensorDTO:
        try:
            raw_sensor = self._repo.save(session, sensor_data)
            return SensorDTO.model_validate(raw_sensor)
        except Exception as e:
            raise DatabaseUnavailableException("Persistence layer rejected target structural sensor assignment block mapping execution.", {"err": str(e)})

    def get_sensor(self, session: Any, sensor_id: UUID) -> SensorDTO:
        record = self._repo.find_by_id(session, sensor_id)
        if not record:
            raise ResourceNotFoundError(f"Sensor entry vector signature '{sensor_id}' not found.")
        return SensorDTO.model_validate(record)

    def list_sensors_by_machine(self, session: Any, machine_id: UUID) -> List[SensorDTO]:
        records = self._repo.find_by_machine(session, machine_id)
        return [SensorDTO.model_validate(r) for r in records]

    def execute_calibration(self, session: Any, sensor_id: UUID, calibration_offset: float) -> SensorDTO:
        record = self._repo.find_by_id(session, sensor_id)
        if not record:
            raise ResourceNotFoundError(f"Sensor tracking node key '{sensor_id}' not discovered.")
        record.calibration_offset = calibration_offset
        updated_record = self._repo.save(session, record)
        return SensorDTO.model_validate(updated_record)

    def lookup_status(self, session: Any, sensor_id: UUID) -> OperationalStatus:
        return self.get_sensor(session, sensor_id).status
