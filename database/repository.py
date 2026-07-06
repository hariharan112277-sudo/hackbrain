"""
Enterprise-grade Repository implementation module mapping execution contexts
for real-time and historical analytics pipelines.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import insert, update

from database.models import Asset, Machine, Sensor, Telemetry, Alarm, MachineEvent, MaintenanceLog
from database.crud import BaseCRUD
from database.interfaces import IRepository
from database.exceptions import BulkOperationError, IOBDatabaseError


class AssetRepository(BaseCRUD[Asset], IRepository[Asset]):
    def __init__(self): super().__init__(Asset)
    def find_by_id(self, session: Session, id_val: UUID) -> Optional[Asset]: return self.get_by_id(session, id_val)
    def save(self, session: Session, entity: Asset) -> Asset: return self.create(session, entity)
    def remove(self, session: Session, id_val: UUID) -> bool: return self.delete(session, id_val)

    def find_by_production_line(self, session: Session, line_id: UUID) -> List[Asset]:
        return session.query(Asset).filter(Asset.production_line_id == line_id, Asset.is_deleted == False).all()


class MachineRepository(BaseCRUD[Machine], IRepository[Machine]):
    def __init__(self): super().__init__(Machine)
    def find_by_id(self, session: Session, id_val: UUID) -> Optional[Machine]: return self.get_by_id(session, id_val)
    def save(self, session: Session, entity: Machine) -> Machine: return self.create(session, entity)
    def remove(self, session: Session, id_val: UUID) -> bool: return self.delete(session, id_val)


class SensorRepository(BaseCRUD[Sensor], IRepository[Sensor]):
    def __init__(self): super().__init__(Sensor)
    def find_by_id(self, session: Session, id_val: UUID) -> Optional[Sensor]: return self.get_by_id(session, id_val)
    def save(self, session: Session, entity: Sensor) -> Sensor: return self.create(session, entity)
    def remove(self, session: Session, id_val: UUID) -> bool: return self.delete(session, id_val)

    def get_machine_sensors(self, session: Session, machine_id: UUID) -> List[Sensor]:
        return session.query(Sensor).filter(Sensor.machine_id == machine_id).all()


class TelemetryRepository(BaseCRUD[Telemetry], IRepository[Telemetry]):
    """Engine optimizing structural real-time and array batch insertion streams."""
    def __init__(self):
        super().__init__(Telemetry)

    def find_by_id(self, session: Session, id_val: UUID) -> Optional[Telemetry]:
        return self.get_by_id(session, id_val)

    def save(self, session: Session, entity: Telemetry) -> Telemetry:
        return self.create(session, entity)

    def remove(self, session: Session, id_val: UUID) -> bool:
        return self.delete(session, id_val)

    def bulk_insert_telemetry(self, session: Session, data_manifest: List[Dict[str, Any]]) -> int:
        """High throughput performance array insertion mechanism bypassing heavy unit iteration cycles."""
        if not data_manifest:
            return 0
        try:
            session.execute(insert(Telemetry), data_manifest)
            session.commit()
            return len(data_manifest)
        except Exception as ex:
            session.rollback()
            raise BulkOperationError("Array segment telemetry frame ingestion operation aborted.", ex)

    def get_historical_window(self, session: Session, sensor_id: UUID, start: datetime, end: datetime) -> List[Telemetry]:
        """Provides access optimizations for historical visualization tracking structures."""
        return session.query(Telemetry).filter(
            Telemetry.sensor_id == sensor_id,
            Telemetry.timestamp >= start,
            Telemetry.timestamp <= end
        ).order_by(Telemetry.timestamp.asc()).all()


class EventRepository(BaseCRUD[MachineEvent], IRepository[MachineEvent]):
    def __init__(self): super().__init__(MachineEvent)
    def find_by_id(self, session: Session, id_val: UUID) -> Optional[MachineEvent]: return self.get_by_id(session, id_val)
    def save(self, session: Session, entity: MachineEvent) -> MachineEvent: return self.create(session, entity)
    def remove(self, session: Session, id_val: UUID) -> bool: return self.delete(session, id_val)


class AlarmRepository(BaseCRUD[Alarm], IRepository[Alarm]):
    def __init__(self): super().__init__(Alarm)
    def find_by_id(self, session: Session, id_val: UUID) -> Optional[Alarm]: return self.get_by_id(session, id_val)
    def save(self, session: Session, entity: Alarm) -> Alarm: return self.create(session, entity)
    def remove(self, session: Session, id_val: UUID) -> bool: return self.delete(session, id_val)

    def get_active_alarms(self, session: Session) -> List[Alarm]:
        return session.query(Alarm).filter(Alarm.state != "CLEARED").all()


class MaintenanceRepository(BaseCRUD[MaintenanceLog], IRepository[MaintenanceLog]):
    def __init__(self): super().__init__(MaintenanceLog)
    def find_by_id(self, session: Session, id_val: UUID) -> Optional[MaintenanceLog]: return self.get_by_id(session, id_val)
    def save(self, session: Session, entity: MaintenanceLog) -> MaintenanceLog: return self.create(session, entity)
    def remove(self, session: Session, id_val: UUID) -> bool: return self.delete(session, id_val)
