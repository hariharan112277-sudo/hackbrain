import time
import pytest
from ingestion.exceptions import TimestampValidationException
from ingestion.timestamp_validator import ChronoTimestampValidator


def test_timestamp_validator_valid_unix():
    validator = ChronoTimestampValidator(max_future_drift_seconds=5.0, max_past_drift_seconds=3600.0)
    now = time.time()
    payload = {"timestamp": now - 10.0}
    result = validator.process(payload)
    assert "_parsed_timestamp" in result
    assert abs(result["_parsed_timestamp"] - (now - 10.0)) < 0.001


def test_timestamp_validator_future_drift():
    validator = ChronoTimestampValidator(max_future_drift_seconds=5.0)
    future_ts = time.time() + 60.0  # 60s in future
    payload = {"timestamp": future_ts}
    with pytest.raises(TimestampValidationException) as exc_info:
        validator.process(payload)
    assert "Future" in str(exc_info.value)


def test_timestamp_validator_past_drift():
    validator = ChronoTimestampValidator(max_past_drift_seconds=300.0)
    old_ts = time.time() - 600.0  # 10 mins old
    payload = {"timestamp": old_ts}
    with pytest.raises(TimestampValidationException) as exc_info:
        validator.process(payload)
    assert "Stale" in str(exc_info.value)
