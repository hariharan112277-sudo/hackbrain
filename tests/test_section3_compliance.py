import json
import time
from datetime import datetime, timezone
from ingestion.config import PipelineConfig
from ingestion.interfaces import InMemoryDatabaseWriter
from ingestion.models import RawTelemetryMessage
from ingestion.pipeline import TelemetryProcessingPipeline
from ingestion.validator import JsonPayloadValidator


def test_section3_schema_validation():
    cfg = PipelineConfig.load_from_dir()
    validator = JsonPayloadValidator(max_payload_size_bytes=cfg.validation_parameters.max_payload_size_bytes)
    now_iso = datetime.now(timezone.utc).isoformat()

    valid_payload = {
        "timestamp": now_iso,
        "asset_id": "ASSET-1001",
        "machine_id": "MACH-2001",
        "sensor_id": "SENS-3001",
        "topic": "gmc/aus/asy/line1/mach1/telemetry/temp1",
        "measurement": "TEMPERATURE",
        "value": 212.0,
        "unit": "FAHRENHEIT",
        "quality": "GOOD",
        "sequence_number": 101,
        "gateway_id": "GW-001",
        "site_id": "SITE-AUS",
        "plant_id": "PLANT-GMC",
        "line_id": "LINE-ASY",
        "metadata": {"zone": "Zone-A"}
    }

    result = validator.process(json.dumps(valid_payload))
    assert result["asset_id"] == "ASSET-1001"
    assert result["measurement"] == "TEMPERATURE"


def test_section3_full_pipeline_execution():
    writer = InMemoryDatabaseWriter()
    pipeline = TelemetryProcessingPipeline()
    dispatcher = pipeline.get_dispatcher()
    if dispatcher:
        dispatcher.register_writer(writer)

    now_seconds = time.time()
    now_iso = datetime.fromtimestamp(now_seconds, timezone.utc).isoformat()

    payload_dict = {
        "timestamp": now_iso,
        "asset_id": "TURB-1001",
        "machine_id": "MACH-2001",
        "sensor_id": "SENS-3001",
        "topic": "gmc/aus/asy/line1/mach1/telemetry/temp1",
        "measurement": "TEMPERATURE",
        "value": 212.0,
        "unit": "FAHRENHEIT",
        "quality": "GOOD",
        "sequence_number": 101,
        "gateway_id": "GW-001",
        "site_id": "SITE-AUS",
        "plant_id": "PLANT-GMC",
        "line_id": "LINE-ASY",
        "metadata": {"zone": "Zone-A"}
    }

    raw_msg = RawTelemetryMessage(
        topic="gmc/aus/asy/line1/mach1/telemetry/temp1",
        payload=json.dumps(payload_dict).encode("utf-8")
    )

    model = pipeline.process_raw_message(raw_msg)
    assert model is not None
    assert model.asset_id == "TURB-1001"
    assert model.machine_id == "MACH-2001"
    assert model.sensor_id == "SENS-3001"
    assert model.sequence_number == 101
    # Verify normalization lambda: 212 FAHRENHEIT -> 100.0 CELSIUS
    assert model.normalized_value == 100.0
    assert model.normalized_unit == "CELSIUS"
    # Verify ISA-95 hierarchy extraction from Section 3 fields
    assert model.isa95_hierarchy.site == "SITE-AUS"
    assert model.isa95_hierarchy.area == "PLANT-GMC"
    assert model.isa95_hierarchy.line == "LINE-ASY"
    assert len(writer.records) == 1
