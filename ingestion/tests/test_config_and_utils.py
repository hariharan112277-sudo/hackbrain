import os
from ingestion.config import PipelineConfig
from ingestion.logger import get_logger, AuditLogger
from ingestion.utils import compute_payload_fingerprint, parse_isa95_topic, DeadLetterQueueRecorder


def test_pipeline_config_load():
    cfg = PipelineConfig.load_from_dir()
    assert cfg.mqtt.broker_port == 1883
    assert "TEMPERATURE" in cfg.units_conversions or "temperature" in cfg.units_conversions or cfg.duplicate_window_seconds == 60.0


def test_compute_payload_fingerprint():
    fp1 = compute_payload_fingerprint({"a": 1, "b": 2})
    fp2 = compute_payload_fingerprint({"b": 2, "a": 1})
    assert fp1 == fp2


def test_parse_isa95_topic():
    res = parse_isa95_topic("site1/area1/line1/turbine-01/telemetry")
    assert res["site"] == "site1"
    assert res["equipment"] == "turbine-01"


def test_logger_and_audit():
    logger = get_logger("TestLogger", use_json=True)
    audit = AuditLogger(logger)
    audit.log_security_event("TEST_VIOLATION", "Testing audit log")
    audit.log_pipeline_stage("TestStage", "SUCCESS", duration_ms=1.5)


def test_dlq_recorder(tmp_path):
    dlq = DeadLetterQueueRecorder(dlq_dir=str(tmp_path))
    dlq.record_failure("raw packet data", ValueError("Test failure"))
    assert len(dlq.memory_dlq) == 1
    files = os.listdir(str(tmp_path))
    assert len(files) == 1
