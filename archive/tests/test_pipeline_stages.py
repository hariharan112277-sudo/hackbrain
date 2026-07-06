"""
Phase 10 Operational Handover & Disaster Recovery Verification Test Suite.
Validates post-recovery pipeline stability and dataset archival continuity.
"""
import os
import uuid
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytest

from database.connection import DatabaseConnectionManager
from database.models import Base, Plant, ProductionLine, Gateway, Asset, Machine, Sensor, Telemetry, OperationalStatus
from datasets.pipeline import PreparationPipelineOrchestrator
from integration.registry import MachineRegistryService


def test_post_recovery_system_health_and_archival(tmp_path):
    """Verifies Task 4 disaster recovery validation check and Task 1 cross-team handoffs."""
    db_mgr = DatabaseConnectionManager(db_url="sqlite:///:memory:")
    Base.metadata.create_all(db_mgr.engine)
    session = db_mgr.get_session()

    try:
        plant = Plant(id=uuid.uuid4(), name="Recovery-Plant", location="Munich")
        line = ProductionLine(id=uuid.uuid4(), plant_id=plant.id, name="Recovery-Line", sequence_number=1)
        gw = Gateway(id=uuid.uuid4(), name="Recovery-GW", ip_address="10.0.0.1", mac_address="10:20:30:40:50:60", firmware_version="v6")
        asset = Asset(
            id=uuid.uuid4(), production_line_id=line.id, name="Recovery-Asset", category="Robotics",
            manufacturer="ABB", model="IRB", serial_number="SN-RECOVERY-01", criticality="High",
            installation_date=datetime.now(timezone.utc)
        )
        machine = Machine(id=uuid.uuid4(), asset_id=asset.id, gateway_id=gw.id, firmware_version="v6.1")
        sensor = Sensor(
            id=uuid.uuid4(), machine_id=machine.id, name="Recovery-Sensor", sensor_type="Vibration",
            measurement_unit="mm/s", sampling_rate_hz=100.0
        )
        now = datetime.now(timezone.utc)
        t1 = Telemetry(id=uuid.uuid4(), timestamp=now - timedelta(minutes=5), machine_id=machine.id, sensor_id=sensor.id, measured_value=14.2, sequence_number=1)
        t2 = Telemetry(id=uuid.uuid4(), timestamp=now, machine_id=machine.id, sensor_id=sensor.id, measured_value=14.5, sequence_number=2)
        session.add_all([plant, line, gw, asset, machine, sensor, t1, t2])
        session.commit()

        # Check Member 1 Service Integration post-recovery
        from database.repository import MachineRepository
        m_service = MachineRegistryService(machine_repo=MachineRepository())
        m_dto = m_service.get_machine(session, machine.id)
        assert m_dto.status == OperationalStatus.ONLINE

        # Execute Member 3 Dataset Archival Generation
        archive_dir = str(tmp_path / "phase10_archive_datasets")
        orchestrator = PreparationPipelineOrchestrator(db_mgr.engine, output_dir=archive_dir)
        manifest = orchestrator.run_execution_sequence("2020-01-01T00:00:00Z", "2030-01-01T00:00:00Z")

        assert manifest["pipeline_run_version"] == "v1.0.0"
        hist_file = os.path.join(archive_dir, "historical.csv")
        assert os.path.exists(hist_file)
        df_hist = pd.read_csv(hist_file)
        assert not df_hist.empty

    finally:
        session.close()
        db_mgr.shutdown()
