"""
Integration Architecture Usage Reference Blueprint for Member 1.
Demonstrates structural Dependency Injection using the concrete services layer.
"""
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta

from integration.interfaces import IMachineRepository, ITelemetryRepository, IAlarmRepository, IEventRepository, IMaintenanceRepository
from integration.contracts import QueryCriteriaDTO, TelemetryDTO, MachineDTO
from integration.registry import MachineRegistryService
from integration.query_service import HistoricalQueryService

# --- Structural Mock Framework Drivers for Verification Testing ---


class MockMachineEntity:
    def __init__(self, machine_id: UUID):
        self.id = machine_id
        self.asset_id = uuid4()
        self.gateway_id = uuid4()
        self.firmware_version = "v4.12.0-build99"
        self.operating_hours = 1245.8
        self.runtime_counter = 450.2
        self.current_mode = "AUTOMATIC"
        self.status = "ONLINE"
        self.capabilities = ["HIGH_SPEED_MILLING", "THERMAL_COMPENSATION"]
        self.relationships = {"parent_cell_id": uuid4()}
        self.health_score = 94.6
        self.metadata_fields = {"factory_floor_zone": "A-3"}


class MockTelemetryEntity:
    def __init__(self, sensor_id: UUID, val: float):
        self.id = uuid4()
        self.timestamp = datetime.now(timezone.utc)
        self.machine_id = uuid4()
        self.sensor_id = sensor_id
        self.measured_value = val
        self.quality_code = 192
        self.alarm_status = "NORMAL"
        self.sequence_number = 88201
        self.metadata_fields = {}


class ConcreteMachineRepoMock(IMachineRepository):
    def find_by_id(self, session: Any, machine_id: UUID) -> Optional[Any]:
        return MockMachineEntity(machine_id)
    def get_all_paginated(self, session: Any, skip: int, limit: int) -> List[Any]: return []
    def save(self, session: Any, machine_entity: Any) -> Any: return machine_entity


class ConcreteTelemetryRepoMock(ITelemetryRepository):
    def find_latest_by_sensor(self, session: Any, sensor_id: UUID) -> Optional[Any]: return None
    def find_latest_by_machine(self, session: Any, machine_id: UUID) -> List[Any]: return []
    def get_time_range(self, session: Any, sensor_id: UUID, start: datetime, end: datetime) -> List[Any]:
        return [MockTelemetryEntity(sensor_id, 24.51), MockTelemetryEntity(sensor_id, 24.68)]


# --- Application Layer Integration Workflow Sample Execution Pipeline ---

def execute_downstream_backend_api_simulation():
    """
    Simulates a programmatic interface sequence invoked inside Member 1's routers.
    """
    # 1. Initialize Mock Context Session Tokens (Managed via FastAPI Depends context layers)
    mock_db_context_session = "SQLAlchemySessionScopeInstance"

    # 2. Wire Infrastructure Repositories
    machine_infra_repo = ConcreteMachineRepoMock()
    telemetry_infra_repo = ConcreteTelemetryRepoMock()

    # 3. Instantiate Architecture Services Tier Abstractions
    registry_service = MachineRegistryService(machine_repo=machine_infra_repo)
    historical_query_service = HistoricalQueryService(
        telemetry_repo=telemetry_infra_repo, alarm_repo=None, event_repo=None, maintenance_repo=None
    )

    # WORKFLOW A: Fetching Machine Structural Assets and Configuration Registries
    target_machine_token = UUID("182bcfb2-4d1a-4da2-9b24-9dfc120fb211")
    machine_record_dto: MachineDTO = registry_service.get_machine(mock_db_context_session, target_machine_token)

    print(f"[API Simulation Logging] Machine Entity DTO successfully verified.")
    print(f" -> Mode: {machine_record_dto.current_mode} | Operational Health Score: {machine_record_dto.health_score}%")
    print(f" -> Systems Capability Elements: {machine_record_dto.capabilities}")

    # WORKFLOW B: Processing Historical Sub-Window Queries
    target_sensor_token = UUID("bd5bcefa-9fa1-4191-88bc-41829daff911")
    query_criteria = QueryCriteriaDTO(
        start_time=datetime.now(timezone.utc) - timedelta(days=1),
        end_time=datetime.now(timezone.utc),
        page=1, limit=50
    )

    telemetry_dataset: List[TelemetryDTO] = historical_query_service.get_historical_telemetry(
        session=mock_db_context_session, sensor_id=target_sensor_token, criteria=query_criteria
    )

    print(f"[API Simulation Logging] Discovered historical telemetry frame dataset length: {len(telemetry_dataset)}")
    for element in telemetry_dataset:
        print(f" -> Ingestion Time: {element.timestamp} | Metric Value Capture: {element.measured_value}")


if __name__ == "__main__":
    execute_downstream_backend_api_simulation()
