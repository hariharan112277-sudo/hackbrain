"""
Entity to DTO Mapper Utilities for the Integration Layer.
Converts Phase 5 SQLAlchemy ORM models / dictionaries into immutable Phase 6 DTOs.
"""
from typing import Any, Dict
from uuid import UUID
from datetime import datetime, timezone
from integration.contracts import (
    AssetDTO, MachineDTO, SensorDTO, TelemetryDTO,
    AlarmDTO, MachineEventDTO, MaintenanceLogDTO,
    OperationalStatus, AlarmSeverity, AlarmState
)


class EntityDTOMapper:
    """Provides stateless mapping methods from database models to clean DTOs."""

    @staticmethod
    def to_asset_dto(entity: Any) -> AssetDTO:
        return AssetDTO(
            id=entity.id,
            production_line_id=entity.production_line_id,
            name=entity.name,
            category=entity.category,
            manufacturer=entity.manufacturer,
            model=entity.model,
            serial_number=entity.serial_number,
            criticality=entity.criticality,
            installation_date=entity.installation_date,
            commission_date=getattr(entity, "commission_date", None),
            status=OperationalStatus(str(entity.status.value if hasattr(entity.status, "value") else entity.status)),
            metadata_fields=getattr(entity, "metadata_fields", {})
        )

    @staticmethod
    def to_machine_dto(entity: Any) -> MachineDTO:
        status_val = OperationalStatus.ONLINE
        if hasattr(entity, "asset") and entity.asset:
            status_val = OperationalStatus(str(entity.asset.status.value if hasattr(entity.asset.status, "value") else entity.asset.status))
        return MachineDTO(
            id=entity.id,
            asset_id=entity.asset_id,
            gateway_id=entity.gateway_id,
            firmware_version=entity.firmware_version,
            operating_hours=float(entity.operating_hours),
            runtime_counter=float(entity.runtime_counter),
            current_mode=entity.current_mode,
            status=status_val,
            capabilities=["AUTO_MODE", "VIBRATION_MONITORING", "THERMAL_LOGGING"],
            relationships={"asset_id": entity.asset_id, "gateway_id": entity.gateway_id},
            health_score=98.5,
            metadata_fields={}
        )

    @staticmethod
    def to_sensor_dto(entity: Any) -> SensorDTO:
        return SensorDTO(
            id=entity.id,
            machine_id=entity.machine_id,
            name=entity.name,
            sensor_type=entity.sensor_type,
            measurement_unit=entity.measurement_unit,
            sampling_rate_hz=float(entity.sampling_rate_hz),
            calibration_offset=float(getattr(entity, "calibration_offset", 0.0)),
            lower_threshold=getattr(entity, "lower_threshold", None),
            upper_threshold=getattr(entity, "upper_threshold", None),
            status=OperationalStatus(str(entity.status.value if hasattr(entity.status, "value") else entity.status)),
            metadata_fields=getattr(entity, "metadata_fields", {})
        )

    @staticmethod
    def to_telemetry_dto(entity: Any) -> TelemetryDTO:
        return TelemetryDTO(
            id=entity.id,
            timestamp=entity.timestamp,
            machine_id=entity.machine_id,
            sensor_id=entity.sensor_id,
            measured_value=float(entity.measured_value),
            quality_code=int(getattr(entity, "quality_code", 192)),
            alarm_status=str(getattr(entity, "alarm_status", "NORMAL")),
            sequence_number=int(getattr(entity, "sequence_number", 1)),
            metadata_fields=getattr(entity, "metadata_fields", {})
        )

    @staticmethod
    def to_alarm_dto(entity: Any) -> AlarmDTO:
        return AlarmDTO(
            id=entity.id,
            machine_id=entity.machine_id,
            sensor_id=entity.sensor_id,
            severity=AlarmSeverity(str(entity.severity.value if hasattr(entity.severity, "value") else entity.severity)),
            state=AlarmState(str(entity.state.value if hasattr(entity.state, "value") else entity.state)),
            trigger_timestamp=entity.trigger_timestamp,
            ack_timestamp=getattr(entity, "ack_timestamp", None),
            clear_timestamp=getattr(entity, "clear_timestamp", None),
            trigger_value=float(entity.trigger_value),
            threshold_violated=entity.threshold_violated,
            operator_notes=getattr(entity, "operator_notes", None)
        )
