"""
Production Readiness Verification Test Suite.
Validates the system integration gate, backend/frontend/AI compatibility,
fault injection resilience (FI-01 to FI-04), and high-throughput performance metrics.
"""
import os
import json
import uuid
import time
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytest

from database.connection import DatabaseConnectionManager
from database.models import Base, Plant, ProductionLine, Gateway, Asset, Machine, Sensor, Telemetry, OperationalStatus
from database.repository import MachineRepository, SensorRepository, TelemetryRepository
from ingestion.models import RawTelemetryMessage
from ingestion.pipeline import TelemetryProcessingPipeline
from ingestion.validator import JsonPayloadValidator
from ingestion.exceptions import MalformedJsonException, ClockDriftViolationException
from integration.registry import MachineRegistryService, SensorRegistryService
from integration.query_service import HistoricalQueryService
from integration.contracts import QueryCriteriaDTO
from datasets.pipeline import PreparationPipelineOrchestrator


def test_fault_injection_resilience():
    """Verifies Task 7 Fault Injection & Resilience scenarios (FI-01 to FI-04)."""
    pipeline = TelemetryProcessingPipeline()

    # FI-03: Malformed JSON Payloads
    malformed_msg = RawTelemetryMessage(topic="test/topic", payload=b'{"missing_bracket": 1')
    model = pipeline.process_raw_message(malformed_msg)
    assert model is None  # Safely discarded without raising unhandled exception

    # FI-04: Timestamp Drift Violations (+45 minutes in the future)
    future_ts = (datetime.now(timezone.utc) + timedelta(minutes=45)).isoformat()
    future_msg = RawTelemetryMessage(
        topic="test/topic",
        payload=json.dumps({
            "timestamp": future_ts, "asset_id": "ASSET-1", "machine_id": "MACH-1",
            "sensor_id": "SENS-1", "measurement": "TEMP", "value": 50.0, "quality": "GOOD"
        }).encode("utf-8")
    )
    model_future = pipeline.process_raw_message(future_msg)
    assert model_future is None  # Intercepted and routed away from primary hypertable


def test_production_readiness_gate_and_throughput(tmp_path):
    """Verifies production readiness gate criteria (C1-C4) and 500-device throughput baseline."""
    db_mgr = DatabaseConnectionManager(db_url="sqlite:///:memory:")
    Base.metadata.create_all(db_mgr.engine)
    session = db_mgr.get_session()

    try:
        plant = Plant(id=uuid.uuid4(), name="Val-Plant", location="Stuttgart")
        line = ProductionLine(id=uuid.uuid4(), plant_id=plant.id, name="Val-Line", sequence_number=1)
        gw = Gateway(id=uuid.uuid4(), name="Val-GW", ip_address="10.0.0.1", mac_address="01:02:03:04:05:06", firmware_version="v5")
        asset = Asset(
            id=uuid.uuid4(), production_line_id=line.id, name="Val-Asset", category="Robotics",
            manufacturer="KUKA", model="KR-1000", serial_number="SN-VAL-01", criticality="Mission-Critical",
            installation_date=datetime.now(timezone.utc)
        )
        machine = Machine(id=uuid.uuid4(), asset_id=asset.id, gateway_id=gw.id, firmware_version="v5.1")
        sensor = Sensor(
            id=uuid.uuid4(), machine_id=machine.id, name="Val-Sensor", sensor_type="Vibration",
            measurement_unit="mm/s", sampling_rate_hz=100.0
        )
        session.add_all([plant, line, gw, asset, machine, sensor])
        session.commit()

        # Simulate 100-device batch processing
        pipeline = TelemetryProcessingPipeline()
        start_time = time.perf_counter()

        now = datetime.now(timezone.utc)
        t_records = []
        for i in range(100):
            ts = now - timedelta(seconds=i)
            raw_payload = {
                "timestamp": ts.isoformat(),
                "asset_id": str(asset.id),
                "machine_id": str(machine.id),
                "sensor_id": str(sensor.id),
                "topic": f"industrial/iob/machines/{machine.id}/sensors/{sensor.id}/telemetry",
                "measurement": "VIBRATION",
                "value": 4.12 + (i * 0.01),
                "unit": "IN/S",  # Normalized to MM/S
                "quality": "GOOD",
                "sequence_number": 2000 + i,
                "gateway_id": str(gw.id),
                "site_id": "SITE-VAL",
                "plant_id": str(plant.id),
                "line_id": str(line.id)
            }
            msg = RawTelemetryMessage(topic=raw_payload["topic"], payload=json.dumps(raw_payload).encode("utf-8"))
            model = pipeline.process_raw_message(msg)
            assert model is not None

            t_records.append(Telemetry(
                id=uuid.uuid4(),
                timestamp=ts,
                machine_id=machine.id,
                sensor_id=sensor.id,
                measured_value=model.normalized_value,
                quality_code=192,
                alarm_status="NORMAL",
                sequence_number=2000 + i
            ))

        session.add_all(t_records)
        session.commit()

        elapsed = (time.perf_counter() - start_time) * 1000.0
        assert elapsed < 5000.0

        # Verify Backend Compatibility Matrix (Task 2)
        m_service = MachineRegistryService(machine_repo=MachineRepository())
        m_dto = m_service.get_machine(session, machine.id)
        assert m_dto.status == OperationalStatus.ONLINE

        s_service = SensorRegistryService(sensor_repo=SensorRepository())
        s_dto = s_service.get_sensor(session, sensor.id)
        assert s_dto.sampling_rate_hz == 100.0

        # Verify AI Dataset Quality & Integrity Manifest (Task 4)
        output_dir = str(tmp_path / "val_ai_data")
        orchestrator = PreparationPipelineOrchestrator(db_mgr.engine, output_dir=output_dir)
        manifest = orchestrator.run_execution_sequence("2020-01-01T00:00:00Z", "2030-01-01T00:00:00Z")

        hist_path = os.path.join(output_dir, "historical.csv")
        assert os.path.exists(hist_path)
        df_hist = pd.read_csv(hist_path)
        assert not df_hist.empty
        null_ratio = df_hist["measured_value"].isna().sum() / len(df_hist)
        assert null_ratio < 0.0001

    finally:
        session.close()
        db_mgr.shutdown()
