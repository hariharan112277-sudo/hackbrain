import os
import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import pytest

from database.connection import DatabaseConnectionManager
from database.models import Base, Plant, ProductionLine, Gateway, Asset, Machine, Sensor, Telemetry, Alarm, OperationalStatus
from datasets import (
    IndustrialDataCleaner,
    IndustrialDataTransformer,
    TimeSeriesAggregator,
    IndustrialLabelGenerator,
    DatasetStatisticsProfiler,
    DatasetIntegrityValidator,
    PreparationPipelineOrchestrator
)


def test_cleaner_outlier_and_quality():
    cleaner = IndustrialDataCleaner()
    now = pd.Timestamp("2026-07-03T00:00:00Z")
    df = pd.DataFrame({
        "timestamp": [now, now + pd.Timedelta(minutes=1), now + pd.Timedelta(minutes=2), now + pd.Timedelta(minutes=3)],
        "machine_id": ["m1", "m1", "m1", "m1"],
        "sensor_id": ["s1", "s1", "s1", "s1"],
        "measured_value": [10.0, 10.1, 500.0, 10.2],  # 500.0 is outlier
        "quality_code": [192, 192, 192, 64]  # 64 is bad quality
    })
    cleaned = cleaner.purge_and_realign_telemetry(df)
    assert not cleaned.empty
    # Check values after interpolation
    assert cleaned["measured_value"].max() < 100.0


def test_transformer_and_aggregator():
    transformer = IndustrialDataTransformer()
    aggregator = TimeSeriesAggregator()
    now = pd.Timestamp("2026-07-03T00:00:00Z")
    df = pd.DataFrame({
        "timestamp": [now + pd.Timedelta(minutes=i) for i in range(10)],
        "machine_id": ["m1"] * 10,
        "sensor_id": ["s1"] * 10,
        "measured_value": [float(i) for i in range(10)],
        "current_mode": ["PRODUCTION"] * 10
    })
    encoded = transformer.transform_categorical_states(df)
    assert encoded["current_mode_encoded"].iloc[0] == 1

    rolled = aggregator.calculate_rolling_features(encoded, window_sizes=[5])
    assert "rolling_mean_5m" in rolled.columns


def test_label_generator():
    labeler = IndustrialLabelGenerator()
    now = pd.Timestamp("2026-07-03T00:00:00Z")
    t_df = pd.DataFrame({
        "timestamp": [now, now + pd.Timedelta(minutes=60)],
        "machine_id": ["m1", "m1"],
        "sensor_id": ["s1", "s1"],
        "measured_value": [20.0, 25.0]
    })
    f_df = pd.DataFrame({
        "id": ["f1"],
        "timestamp": [now + pd.Timedelta(minutes=90)],
        "machine_id": ["m1"],
        "failure_type": ["HYDRAULIC_LEAK"],
        "category": ["MECHANICAL"],
        "severity": ["HIGH"],
        "operating_hours": [100.0]
    })
    labeled = labeler.append_predictive_maintenance_labels(t_df, f_df)
    assert labeled.iloc[1]["failure_binary_target"] == 1
    assert labeled.iloc[1]["failure_category_target"] == "HYDRAULIC_LEAK"


def test_statistics_and_validator():
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-07-03T00:00:00Z")],
        "machine_id": ["m1"],
        "sensor_id": ["s1"],
        "measured_value": [42.5],
        "failure_binary_target": [0]
    })
    profile = DatasetStatisticsProfiler.generate_comprehensive_profile(df)
    assert profile["total_record_count"] == 1
    assert profile["statistical_summary_metrics"]["mean"] == 42.5

    report = DatasetIntegrityValidator.validate_dataset_schema(df, ['timestamp', 'machine_id'])
    assert report["validation_passed_indicator"] is True


def test_full_pipeline_orchestrator(tmp_path):
    db_mgr = DatabaseConnectionManager(db_url="sqlite:///:memory:")
    Base.metadata.create_all(db_mgr.engine)
    session = db_mgr.get_session()
    try:
        plant = Plant(id=uuid.uuid4(), name="Data-Plant", location="Stuttgart")
        line = ProductionLine(id=uuid.uuid4(), plant_id=plant.id, name="Data-Line", sequence_number=1)
        gw = Gateway(id=uuid.uuid4(), name="Data-GW", ip_address="10.0.0.1", mac_address="11:22:33:44:55:66", firmware_version="v1")
        asset = Asset(
            id=uuid.uuid4(), production_line_id=line.id, name="Data-Asset", category="Robotics",
            manufacturer="ABB", model="IRB", serial_number="SN-DATA-01", criticality="High",
            installation_date=datetime.now(timezone.utc)
        )
        machine = Machine(id=uuid.uuid4(), asset_id=asset.id, gateway_id=gw.id, firmware_version="v2")
        sensor = Sensor(id=uuid.uuid4(), machine_id=machine.id, name="Data-Sensor", sensor_type="Vibration", measurement_unit="mm/s", sampling_rate_hz=100.0)
        
        now = datetime.now(timezone.utc)
        t1 = Telemetry(id=uuid.uuid4(), timestamp=now - timedelta(minutes=10), machine_id=machine.id, sensor_id=sensor.id, measured_value=12.0, sequence_number=1)
        t2 = Telemetry(id=uuid.uuid4(), timestamp=now, machine_id=machine.id, sensor_id=sensor.id, measured_value=12.5, sequence_number=2)
        session.add_all([plant, line, gw, asset, machine, sensor, t1, t2])
        session.commit()
    finally:
        session.close()

    output_dir = str(tmp_path / "data_output")
    orchestrator = PreparationPipelineOrchestrator(db_mgr.engine, output_dir=output_dir)
    manifest = orchestrator.run_execution_sequence("2020-01-01T00:00:00Z", "2030-01-01T00:00:00Z")
    
    assert manifest["pipeline_run_version"] == "v1.0.0"
    assert os.path.exists(os.path.join(output_dir, "historical.csv"))
    assert os.path.exists(os.path.join(output_dir, "failures.csv"))
    assert os.path.exists(os.path.join(output_dir, "metadata.json"))
    db_mgr.shutdown()
