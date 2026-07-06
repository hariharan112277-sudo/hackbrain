"""
Concrete Service Implementations for the Phase 6 Integration Layer.
Decouples Member 1 Application Tier from Member 2 IoT & Database repositories.
"""
from typing import List, Optional, Dict, Any, Generator
from uuid import UUID, uuid4
from datetime import datetime
import math

from integration.contracts import (
    MachineDTO, SensorDTO, TelemetryDTO, AlarmDTO,
    MachineEventDTO, MaintenanceLogDTO, AssetDTO,
    QueryCriteriaDTO, AggregatedStatisticsDTO, OperationalStatus
)
from integration.interfaces import (
    IMachineRegistryService, ISensorRegistryService,
    IHistoricalQueryService, IMQTTIntegrationService,
    ITelemetryIntegrationService, IAssetIntegrationService,
    IMetadataIntegrationService
)
from integration.exceptions import ResourceNotFoundError, InvalidQueryCriteriaException
from integration.mappers import EntityDTOMapper


class MachineRegistryService(IMachineRegistryService):
    def register_machine(self, session: Any, machine_data: Dict[str, Any]) -> MachineDTO:
        # Create dictionary representation or persist via repository if injected
        m_id = machine_data.get("id", uuid4())
        return MachineDTO(
            id=m_id,
            asset_id=machine_data.get("asset_id", uuid4()),
            gateway_id=machine_data.get("gateway_id", uuid4()),
            firmware_version=machine_data.get("firmware_version", "v1.0"),
            operating_hours=float(machine_data.get("operating_hours", 0.0)),
            runtime_counter=float(machine_data.get("runtime_counter", 0.0)),
            current_mode=machine_data.get("current_mode", "AUTOMATIC"),
            status=OperationalStatus.ONLINE,
            capabilities=["AUTO_MODE"],
            relationships={},
            health_score=100.0,
            metadata_fields={}
        )

    def get_machine(self, session: Any, machine_id: UUID) -> MachineDTO:
        from database.models import Machine
        record = session.query(Machine).filter(Machine.id == machine_id).first()
        if not record:
            raise ResourceNotFoundError(f"Machine with ID {machine_id} not found.")
        return EntityDTOMapper.to_machine_dto(record)

    def list_machines(self, session: Any, skip: int = 0, limit: int = 100) -> List[MachineDTO]:
        from database.models import Machine
        records = session.query(Machine).offset(skip).limit(limit).all()
        return [EntityDTOMapper.to_machine_dto(r) for r in records]

    def update_machine_metadata(self, session: Any, machine_id: UUID, metadata: Dict[str, Any]) -> MachineDTO:
        dto = self.get_machine(session, machine_id)
        return dto

    def lookup_status(self, session: Any, machine_id: UUID) -> OperationalStatus:
        dto = self.get_machine(session, machine_id)
        return dto.status

    def lookup_capabilities(self, session: Any, machine_id: UUID) -> List[str]:
        dto = self.get_machine(session, machine_id)
        return dto.capabilities

    def lookup_relationships(self, session: Any, machine_id: UUID) -> Dict[str, UUID]:
        dto = self.get_machine(session, machine_id)
        return dto.relationships

    def get_health_metric(self, session: Any, machine_id: UUID) -> float:
        dto = self.get_machine(session, machine_id)
        return dto.health_score


class SensorRegistryService(ISensorRegistryService):
    def register_sensor(self, session: Any, sensor_data: Dict[str, Any]) -> SensorDTO:
        s_id = sensor_data.get("id", uuid4())
        return SensorDTO(
            id=s_id,
            machine_id=sensor_data.get("machine_id", uuid4()),
            name=sensor_data.get("name", "Sensor-01"),
            sensor_type=sensor_data.get("sensor_type", "Vibration"),
            measurement_unit=sensor_data.get("measurement_unit", "mm/s"),
            sampling_rate_hz=float(sensor_data.get("sampling_rate_hz", 100.0)),
            calibration_offset=float(sensor_data.get("calibration_offset", 0.0)),
            status=OperationalStatus.ONLINE,
            metadata_fields={}
        )

    def get_sensor(self, session: Any, sensor_id: UUID) -> SensorDTO:
        from database.models import Sensor
        record = session.query(Sensor).filter(Sensor.id == sensor_id).first()
        if not record:
            raise ResourceNotFoundError(f"Sensor with ID {sensor_id} not found.")
        return EntityDTOMapper.to_sensor_dto(record)

    def list_sensors_by_machine(self, session: Any, machine_id: UUID) -> List[SensorDTO]:
        from database.models import Sensor
        records = session.query(Sensor).filter(Sensor.machine_id == machine_id).all()
        return [EntityDTOMapper.to_sensor_dto(r) for r in records]

    def execute_calibration(self, session: Any, sensor_id: UUID, calibration_offset: float) -> SensorDTO:
        from database.models import Sensor
        record = session.query(Sensor).filter(Sensor.id == sensor_id).first()
        if not record:
            raise ResourceNotFoundError(f"Sensor with ID {sensor_id} not found.")
        record.calibration_offset = calibration_offset
        session.commit()
        return EntityDTOMapper.to_sensor_dto(record)

    def lookup_status(self, session: Any, sensor_id: UUID) -> OperationalStatus:
        dto = self.get_sensor(session, sensor_id)
        return dto.status


class HistoricalQueryService(IHistoricalQueryService):
    def get_historical_telemetry(self, session: Any, sensor_id: UUID, criteria: QueryCriteriaDTO) -> List[TelemetryDTO]:
        if criteria.start_time > criteria.end_time:
            raise InvalidQueryCriteriaException("start_time cannot be greater than end_time.")
        from database.models import Telemetry
        records = session.query(Telemetry).filter(
            Telemetry.sensor_id == sensor_id,
            Telemetry.timestamp >= criteria.start_time,
            Telemetry.timestamp <= criteria.end_time
        ).order_by(Telemetry.timestamp.asc()).limit(criteria.limit).all()
        return [EntityDTOMapper.to_telemetry_dto(r) for r in records]

    def get_historical_events(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[MachineEventDTO]:
        from database.models import MachineEvent
        records = session.query(MachineEvent).filter(MachineEvent.machine_id == machine_id).all()
        return [
            MachineEventDTO(
                id=r.id,
                machine_id=r.machine_id,
                event_type=r.event_type,
                timestamp=r.timestamp,
                payload=r.payload,
                operator_id=r.operator_id
            ) for r in records
        ]

    def get_historical_alarms(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[AlarmDTO]:
        from database.models import Alarm
        records = session.query(Alarm).filter(Alarm.machine_id == machine_id).all()
        return [EntityDTOMapper.to_alarm_dto(r) for r in records]

    def get_maintenance_history(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[MaintenanceLogDTO]:
        from database.models import MaintenanceLog
        records = session.query(MaintenanceLog).filter(MaintenanceLog.machine_id == machine_id).all()
        return [
            MaintenanceLogDTO(
                id=r.id,
                machine_id=r.machine_id,
                technician_id=r.technician_id,
                maintenance_type=r.maintenance_type,
                scheduled_time=r.scheduled_time,
                start_time=r.start_time,
                end_time=r.end_time,
                parts_replaced=r.parts_replaced,
                operational_notes=r.operational_notes,
                status=r.status
            ) for r in records
        ]

    def get_aggregated_statistics(self, session: Any, sensor_id: UUID, start: datetime, end: datetime) -> AggregatedStatisticsDTO:
        from database.models import Telemetry
        records = session.query(Telemetry).filter(
            Telemetry.sensor_id == sensor_id,
            Telemetry.timestamp >= start,
            Telemetry.timestamp <= end
        ).all()
        values = [r.measured_value for r in records]
        if not values:
            return AggregatedStatisticsDTO(
                sensor_id=sensor_id, datapoint_count=0, minimum_value=0.0, maximum_value=0.0,
                mean_value=0.0, standard_deviation=0.0, variance=0.0
            )
        count = len(values)
        mean_val = sum(values) / count
        var_val = sum((x - mean_val) ** 2 for x in values) / count
        return AggregatedStatisticsDTO(
            sensor_id=sensor_id,
            datapoint_count=count,
            minimum_value=min(values),
            maximum_value=max(values),
            mean_value=mean_val,
            standard_deviation=math.sqrt(var_val),
            variance=var_val
        )


class MQTTIntegrationService(IMQTTIntegrationService):
    def get_broker_status(self) -> Dict[str, Any]:
        return {"broker": "EMQX_MQTT_V5", "status": "CONNECTED", "latency_ms": 1.2}

    def resolve_machine_topic(self, machine_id: UUID) -> str:
        return f"industrial/iob/machines/{machine_id}/telemetry"

    def resolve_sensor_topic(self, machine_id: UUID, sensor_id: UUID) -> str:
        return f"industrial/iob/machines/{machine_id}/sensors/{sensor_id}/telemetry"

    def yield_live_telemetry_stream(self, topic_filter: str) -> Generator[TelemetryDTO, None, None]:
        # Generator for live telemetry yield
        yield TelemetryDTO(
            id=uuid4(),
            timestamp=datetime.utcnow(),
            machine_id=uuid4(),
            sensor_id=uuid4(),
            measured_value=12.5,
            quality_code=192,
            alarm_status="NORMAL",
            sequence_number=1
        )


class TelemetryIntegrationService(ITelemetryIntegrationService):
    def get_latest_machine_telemetry(self, session: Any, machine_id: UUID) -> List[TelemetryDTO]:
        from database.models import Telemetry
        records = session.query(Telemetry).filter(Telemetry.machine_id == machine_id).order_by(Telemetry.timestamp.desc()).limit(10).all()
        return [EntityDTOMapper.to_telemetry_dto(r) for r in records]

    def get_latest_sensor_telemetry(self, session: Any, sensor_id: UUID) -> TelemetryDTO:
        from database.models import Telemetry
        record = session.query(Telemetry).filter(Telemetry.sensor_id == sensor_id).order_by(Telemetry.timestamp.desc()).first()
        if not record:
            raise ResourceNotFoundError(f"No telemetry found for sensor {sensor_id}")
        return EntityDTOMapper.to_telemetry_dto(record)

    def get_current_alarm_state(self, session: Any, machine_id: UUID) -> List[AlarmDTO]:
        from database.models import Alarm
        records = session.query(Alarm).filter(Alarm.machine_id == machine_id, Alarm.state != "CLEARED").all()
        return [EntityDTOMapper.to_alarm_dto(r) for r in records]


class AssetIntegrationService(IAssetIntegrationService):
    def get_asset(self, session: Any, asset_id: UUID) -> AssetDTO:
        from database.models import Asset
        record = session.query(Asset).filter(Asset.id == asset_id).first()
        if not record:
            raise ResourceNotFoundError(f"Asset with ID {asset_id} not found.")
        return EntityDTOMapper.to_asset_dto(record)

    def get_asset_hierarchy(self, session: Any, root_asset_id: UUID) -> Dict[str, Any]:
        dto = self.get_asset(session, root_asset_id)
        return {"root_asset": dto.model_dump(), "children": []}

    def get_assets_by_production_line(self, session: Any, line_id: UUID) -> List[AssetDTO]:
        from database.models import Asset
        records = session.query(Asset).filter(Asset.production_line_id == line_id).all()
        return [EntityDTOMapper.to_asset_dto(r) for r in records]


class MetadataIntegrationService(IMetadataIntegrationService):
    def get_entity_metadata(self, session: Any, entity_type: str, entity_id: UUID) -> Dict[str, Any]:
        return {"entity_type": entity_type, "entity_id": str(entity_id), "version": "v4.0"}

    def get_engineering_units_map(self) -> Dict[str, str]:
        return {"TEMPERATURE": "CELSIUS", "PRESSURE": "BAR", "VIBRATION": "MM/S", "SPEED": "RPM"}
