"""
Unit verification suite checking pipeline data cleansing routines and label generation structures.
"""
import pytest
import pandas as pd
import numpy as np
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from datasets.cleaner import IndustrialDataCleaner
from datasets.label_generator import IndustrialLabelGenerator


def test_cleaner_rejection_of_bad_opc_quality_metrics():
    """Verifies that telemetry entries with non-good quality status tracking identifiers are removed."""
    cleaner = IndustrialDataCleaner()

    base_time = datetime.now(timezone.utc)
    mock_data = pd.DataFrame([
        {"timestamp": base_time, "machine_id": "m-1", "sensor_id": "s-1", "measured_value": 44.2, "quality_code": 192},
        {"timestamp": base_time + timedelta(minutes=1), "machine_id": "m-1", "sensor_id": "s-1", "measured_value": 99.9, "quality_code": 0}  # Should be scrubbed
    ])

    processed = cleaner.purge_and_realign_telemetry(mock_data)

    # Assert that missing parameters are filled by interpolation mechanics
    assert not processed['measured_value'].isna().any()
    assert processed.loc[processed['timestamp'] == pd.to_datetime(base_time) + timedelta(minutes=1), 'measured_value'].values[0] == 44.2


def test_label_generator_predictive_window_flags():
    """Verifies that binary classification labels are assigned correctly during countdowns to failure events."""
    base_time = datetime.now(timezone.utc)

    mock_telemetry = pd.DataFrame([
        {"timestamp": base_time, "machine_id": "m-1", "sensor_id": "s-1", "measured_value": 22.1},
        {"timestamp": base_time + timedelta(minutes=100), "machine_id": "m-1", "sensor_id": "s-1", "measured_value": 23.5}
    ])

    mock_failures = pd.DataFrame([
        {"timestamp": base_time + timedelta(minutes=120), "machine_id": "m-1", "failure_type": "MOTOR_OVERHEAT"}
    ])

    labeled = IndustrialLabelGenerator.append_predictive_maintenance_labels(mock_telemetry, mock_failures)

    assert labeled.loc[0, 'failure_binary_target'] == 1  # 120 mins out matches edge limit criteria parameters
    assert labeled.loc[1, 'failure_binary_target'] == 1  # 20 mins out is inside the hazard envelope interval bounds
