import json
import pytest
from ingestion.exceptions import PayloadValidationException
from ingestion.validator import JsonPayloadValidator


def test_json_payload_validator_valid_string():
    validator = JsonPayloadValidator()
    raw_str = json.dumps({
        "message_id": "msg-001",
        "asset_id": "turbine-01",
        "timestamp": 1783000000.0,
        "readings": {"temperature": 75.5}
    })
    result = validator.process(raw_str)
    assert result["message_id"] == "msg-001"
    assert result["readings"]["temperature"] == 75.5


def test_json_payload_validator_valid_bytes():
    validator = JsonPayloadValidator()
    raw_bytes = json.dumps({
        "message_id": "msg-002",
        "asset_id": "compressor-02",
        "timestamp": "2026-07-02T10:00:00Z",
        "readings": {"pressure": 12.0}
    }).encode("utf-8")
    result = validator.process(raw_bytes)
    assert result["asset_id"] == "compressor-02"


def test_json_payload_validator_missing_required_field():
    validator = JsonPayloadValidator()
    invalid_data = {
        "message_id": "msg-003",
        "asset_id": "pump-03"
        # missing timestamp and readings
    }
    with pytest.raises(PayloadValidationException) as exc_info:
        validator.process(invalid_data)
    assert "Missing mandatory fields" in str(exc_info.value)


def test_json_payload_validator_invalid_json_string():
    validator = JsonPayloadValidator()
    with pytest.raises(PayloadValidationException):
        validator.process("{invalid json string")
