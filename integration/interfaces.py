"""
Abstract Domain Interfaces & Repository Specification Protocols.
Establishes system interfaces using Abstract Base Classes (ABCs).
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generator
from uuid import UUID
from datetime import datetime

from integration.contracts import (
    MachineDTO, SensorDTO, TelemetryDTO, AlarmDTO,
    MachineEventDTO, MaintenanceLogDTO, AssetDTO,
    QueryCriteriaDTO, AggregatedStatisticsDTO, OperationalStatus
)

# --- Persistence Layer Abstractions (For Repository Implementation Isolation) ---


class IMachineRepository(ABC):
    @abstractmethod
    def find_by_id(self, session: Any, machine_id: UUID) -> Optional[Any]: pass
    @abstractmethod
    def get_all_paginated(self, session: Any, skip: int, limit: int) -> List[Any]: pass
    @abstractmethod
    def save(self, session: Any, machine_entity: Any) -> Any: pass


class ISensorRepository(ABC):
    @abstractmethod
    def find_by_id(self, session: Any, sensor_id: UUID) -> Optional[Any]: pass
    @abstractmethod
    def find_by_machine(self, session: Any, machine_id: UUID) -> List[Any]: pass
    @abstractmethod
    def save(self, session: Any, sensor_entity: Any) -> Any: pass


class ITelemetryRepository(ABC):
    @abstractmethod
    def find_latest_by_sensor(self, session: Any, sensor_id: UUID) -> Optional[Any]: pass
    @abstractmethod
    def find_latest_by_machine(self, session: Any, machine_id: UUID) -> List[Any]: pass
    @abstractmethod
    def get_time_range(self, session: Any, sensor_id: UUID, start: datetime, end: datetime) -> List[Any]: pass


class IAlarmRepository(ABC):
    @abstractmethod
    def get_active_by_machine(self, session: Any, machine_id: UUID) -> List[Any]: pass
    @abstractmethod
    def get_historical_window(self, session: Any, machine_id: UUID, start: datetime, end: datetime) -> List[Any]: pass


class IEventRepository(ABC):
    @abstractmethod
    def get_historical_window(self, session: Any, machine_id: UUID, start: datetime, end: datetime) -> List[Any]: pass


class IMaintenanceRepository(ABC):
    @abstractmethod
    def get_historical_window(self, session: Any, machine_id: UUID, start: datetime, end: datetime) -> List[Any]: pass


class IAssetRepository(ABC):
    @abstractmethod
    def find_by_id(self, session: Any, asset_id: UUID) -> Optional[Any]: pass
    @abstractmethod
    def find_by_production_line(self, session: Any, line_id: UUID) -> List[Any]: pass


# --- Integration Service Tier Contracts (Directly Consumed By Member 1) ---

class IMachineRegistryService(ABC):
    @abstractmethod
    def register_machine(self, session: Any, machine_data: Dict[str, Any]) -> MachineDTO: pass
    @abstractmethod
    def get_machine(self, session: Any, machine_id: UUID) -> MachineDTO: pass
    @abstractmethod
    def list_machines(self, session: Any, skip: int, limit: int) -> List[MachineDTO]: pass
    @abstractmethod
    def update_machine_metadata(self, session: Any, machine_id: UUID, metadata: Dict[str, Any]) -> MachineDTO: pass
    @abstractmethod
    def lookup_status(self, session: Any, machine_id: UUID) -> OperationalStatus: pass
    @abstractmethod
    def lookup_capabilities(self, session: Any, machine_id: UUID) -> List[str]: pass
    @abstractmethod
    def lookup_relationships(self, session: Any, machine_id: UUID) -> Dict[str, UUID]: pass
    @abstractmethod
    def get_health_metric(self, session: Any, machine_id: UUID) -> float: pass


class ISensorRegistryService(ABC):
    @abstractmethod
    def register_sensor(self, session: Any, sensor_data: Dict[str, Any]) -> SensorDTO: pass
    @abstractmethod
    def get_sensor(self, session: Any, sensor_id: UUID) -> SensorDTO: pass
    @abstractmethod
    def list_sensors_by_machine(self, session: Any, machine_id: UUID) -> List[SensorDTO]: pass
    @abstractmethod
    def execute_calibration(self, session: Any, sensor_id: UUID, calibration_offset: float) -> SensorDTO: pass
    @abstractmethod
    def lookup_status(self, session: Any, sensor_id: UUID) -> OperationalStatus: pass


class IHistoricalQueryService(ABC):
    @abstractmethod
    def get_historical_telemetry(self, session: Any, sensor_id: UUID, criteria: QueryCriteriaDTO) -> List[TelemetryDTO]: pass
    @abstractmethod
    def get_historical_events(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[MachineEventDTO]: pass
    @abstractmethod
    def get_historical_alarms(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[AlarmDTO]: pass
    @abstractmethod
    def get_maintenance_history(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[MaintenanceLogDTO]: pass
    @abstractmethod
    def get_aggregated_statistics(self, session: Any, sensor_id: UUID, start: datetime, end: datetime) -> AggregatedStatisticsDTO: pass


class IMQTTIntegrationService(ABC):
    @abstractmethod
    def get_broker_status(self) -> Dict[str, Any]: pass
    @abstractmethod
    def resolve_machine_topic(self, machine_id: UUID) -> str: pass
    @abstractmethod
    def resolve_sensor_topic(self, machine_id: UUID, sensor_id: UUID) -> str: pass
    @abstractmethod
    def yield_live_telemetry_stream(self, topic_filter: str) -> Generator[TelemetryDTO, None, None]: pass


class ITelemetryIntegrationService(ABC):
    @abstractmethod
    def get_latest_machine_telemetry(self, session: Any, machine_id: UUID) -> List[TelemetryDTO]: pass
    @abstractmethod
    def get_latest_sensor_telemetry(self, session: Any, sensor_id: UUID) -> TelemetryDTO: pass
    @abstractmethod
    def get_current_alarm_state(self, session: Any, machine_id: UUID) -> List[AlarmDTO]: pass


class IAssetIntegrationService(ABC):
    @abstractmethod
    def get_asset(self, session: Any, asset_id: UUID) -> AssetDTO: pass
    @abstractmethod
    def get_asset_hierarchy(self, session: Any, root_asset_id: UUID) -> Dict[str, Any]: pass
    @abstractmethod
    def get_assets_by_production_line(self, session: Any, line_id: UUID) -> List[AssetDTO]: pass


class IMetadataIntegrationService(ABC):
    @abstractmethod
    def get_entity_metadata(self, session: Any, entity_type: str, entity_id: UUID) -> Dict[str, Any]: pass
    @abstractmethod
    def get_engineering_units_map(self) -> Dict[str, str]: pass
