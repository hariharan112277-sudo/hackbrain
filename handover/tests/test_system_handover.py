"""
System Handover End-to-End Verification Test Suite.
Validates the interoperability of Phase 4 Ingestion, Phase 5 Storage,
Phase 6 Integration Services, and Phase 7 Dataset Preparation.
"""
import os
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
import pytest
import jsonschema

from database.connection import DatabaseConnectionManager
from database.session import EnterpriseDBSessionScope
from database.repositories import MachineSQLRepository
from database.models import Base, Plant, ProductionLine, Gateway, Asset, Machine, Sensor, OperationalStatus
from database.repository import MachineRepository, TelemetryRepository, AlarmRepository, EventRepository, MaintenanceRepository
from ingestion.models import RawTelemetryMessage
from ingestion.pipeline import TelemetryProcessingPipeline
from integration.registry import MachineRegistryService, SensorRegistryService
from integration.query_service import HistoricalQueryService
from integration.contracts import QueryCriteriaDTO
from datasets.pipeline import PreparationPipelineOrchestrator


def test_mqtt_schema_contract_validation():
    """Verifies Task 4 strict JSON schema validation for Task 3 production MQTT examples."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    telemetry_schema_path = os.path.join(base_dir, "schemas", "iob_telemetry_v1.json")
    alarm_schema_path = os.path.join(base_dir, "schemas", "iob_alarm_v1.json")

    with open(telemetry_schema_path, "r", encoding="utf-8") as f:
        telemetry_schema = json.load(f)
    with open(alarm_schema_path, "r", encoding="utf-8") as f:
        alarm_schema = json.load(f)

    # Task 3 Edge Telemetry Data Packet
    telemetry_example = {
        "timestamp": "2026-07-03T13:53:11.002Z",
        "machine_id": "8c4b18c0-51a2-4db0-96ef-2782bcfb2111",
        "sensor_id": "d09a8f4c-11b2-4911-88bc-41829daff901",
        "measured_value": 78.43,
        "quality_code": 192,
        "sequence_number": 449201
    }
    jsonschema.validate(instance=telemetry_example, schema=telemetry_schema)

    # Verify additionalProperties: false rejects unauthorized attributes
    invalid_telemetry = dict(telemetry_example)
    invalid_telemetry["unauthorized_field"] = "hack"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_telemetry, schema=telemetry_schema)

    # Task 3 Equipment Failure Alarm Packet
    alarm_example = {
        "id": "e0b8a4f2-51a2-4011-87bc-22910daff212",
        "machine_id": "8c4b18c0-51a2-4db0-96ef-2782bcfb2111",
        "sensor_id": "d09a8f4c-11b2-4911-88bc-41829daff901",
        "severity": "CRITICAL",
        "state": "ACTIVE",
        "trigger_timestamp": "2026-07-03T13:53:11.005Z",
        "trigger_value": 112.5,
        "threshold_violated": "upper_threshold_limit"
    }
    jsonschema.validate(instance=alarm_example, schema=alarm_schema)


def test_member1_programmatic_initialization_blueprint():
    """Verifies Task 5 Member 1 initialization blueprint using EnterpriseDBSessionScope and MachineSQLRepository."""
    db_mgr = DatabaseConnectionManager(db_url="sqlite:///:memory:")
    Base.metadata.create_all(db_mgr.engine)
    session = db_mgr.get_session()
    try:
        plant = Plant(id=uuid.uuid4(), name="Blueprint-Plant", location="Berlin")
        line = ProductionLine(id=uuid.uuid4(), plant_id=plant.id, name="Blueprint-Line", sequence_number=1)
        gw = Gateway(id=uuid.uuid4(), name="Blueprint-GW", ip_address="10.20.20.1", mac_address="12:34:56:78:9A:BC", firmware_version="v1")
        asset = Asset(
            id=uuid.uuid4(), production_line_id=line.id, name="Blueprint-Asset", category="Thermal",
            manufacturer="ABB", model="T-100", serial_number="SN-BLUEPRINT-01", criticality="Medium",
            installation_date=datetime.now(timezone.utc)
        )
        target_machine_id = uuid.uuid4()
        machine = Machine(id=target_machine_id, asset_id=asset.id, gateway_id=gw.id, firmware_version="v2.0")
        session.add_all([plant, line, gw, asset, machine])
        session.commit()
    finally:
        session.close()

    # Member 1 Blueprint verification
    service = MachineRegistryService(machine_repo=MachineSQLRepository())
    with EnterpriseDBSessionScope() as active_session:
        machine_dto = service.get_machine(active_session, target_machine_id)
        result_dict = machine_dto.model_dump()
        assert result_dict["id"] == target_machine_id
        assert result_dict["current_mode"] == "AUTOMATIC"

    db_mgr.shutdown()


def test_end_to_end_enterprise_handover(tmp_path):
    # 1. Setup Phase 5 Database Engine
    db_mgr = DatabaseConnectionManager(db_url="sqlite:///:memory:")
    Base.metadata.create_all(db_mgr.engine)
    session = db_mgr.get_session()

    try:
        # Seed core asset hierarchy
        plant = Plant(id=uuid.uuid4(), name="Handover-Plant", location="Frankfurt")
        line = ProductionLine(id=uuid.uuid4(), plant_id=plant.id, name="Handover-Line", sequence_number=1)
        gw = Gateway(id=uuid.uuid4(), name="Handover-GW", ip_address="10.10.10.1", mac_address="FF:EE:DD:CC:BB:AA", firmware_version="v5")
        asset = Asset(
            id=uuid.uuid4(), production_line_id=line.id, name="Handover-Asset", category="Robotics",
            manufacturer="Siemens", model="IRB-6600", serial_number="SN-HANDOVER-99", criticality="High",
            installation_date=datetime.now(timezone.utc)
        )
        machine = Machine(id=uuid.uuid4(), asset_id=asset.id, gateway_id=gw.id, firmware_version="v5.1")
        sensor = Sensor(
            id=uuid.uuid4(), machine_id=machine.id, name="Handover-Sensor", sensor_type="Temperature",
            measurement_unit="Fahrenheit", sampling_rate_hz=10.0
        )
        session.add_all([plant, line, gw, asset, machine, sensor])
        session.commit()

        # 2. Execute Phase 4 Ingestion Pipeline
        pipeline = TelemetryProcessingPipeline()
        now = datetime.now(timezone.utc)
        raw_payload = {
            "timestamp": now.isoformat(),
            "asset_id": str(asset.id),
            "machine_id": str(machine.id),
            "sensor_id": str(sensor.id),
            "topic": f"industrial/iob/machines/{machine.id}/sensors/{sensor.id}/telemetry",
            "measurement": "TEMPERATURE",
            "value": 212.0,  # 212F -> normalized to 100C
            "unit": "FAHRENHEIT",
            "quality": "GOOD",
            "sequence_number": 1001,
            "gateway_id": str(gw.id),
            "site_id": "SITE-HANDOVER",
            "plant_id": str(plant.id),
            "line_id": str(line.id)
        }
        raw_msg = RawTelemetryMessage(
            topic=raw_payload["topic"],
            payload=json.dumps(raw_payload).encode("utf-8")
        )
        model = pipeline.process_raw_message(raw_msg)
        assert model is not None
        assert model.normalized_value == 100.0

        # Persist ingested record into DB
        from database.models import Telemetry
        t_record = Telemetry(
            id=uuid.uuid4(),
            timestamp=now,
            machine_id=machine.id,
            sensor_id=sensor.id,
            measured_value=model.normalized_value,
            quality_code=192,
            alarm_status="NORMAL",
            sequence_number=1001
        )
        session.add(t_record)
        session.commit()

        # 3. Verify Phase 6 Integration Services Consumption
        m_service = MachineRegistryService(machine_repo=MachineRepository())
        m_dto = m_service.get_machine(session, machine.id)
        assert m_dto.status == OperationalStatus.ONLINE

        q_service = HistoricalQueryService(
            telemetry_repo=TelemetryRepository(),
            alarm_repo=AlarmRepository(),
            event_repo=EventRepository(),
            maintenance_repo=MaintenanceRepository()
        )
        criteria = QueryCriteriaDTO(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            page=1, limit=10
        )
        t_dtos = q_service.get_historical_telemetry(session, sensor.id, criteria)
        assert len(t_dtos) == 1
        assert t_dtos[0].measured_value == 100.0

        # 4. Execute Phase 7 Dataset Preparation Pipeline
        output_dir = str(tmp_path / "handover_ai_datasets")
        orchestrator = PreparationPipelineOrchestrator(db_mgr.engine, output_dir=output_dir)
        manifest = orchestrator.run_execution_sequence("2020-01-01T00:00:00Z", "2030-01-01T00:00:00Z")
        assert manifest["pipeline_run_version"] == "v1.0.0"
        assert os.path.exists(os.path.join(output_dir, "historical.csv"))
        assert os.path.exists(os.path.join(output_dir, "metadata.json"))

    finally:
        session.close()
        db_mgr.shutdown()
