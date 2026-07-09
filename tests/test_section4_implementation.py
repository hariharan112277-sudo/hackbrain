import json
import time
from datetime import datetime
from ingestion.config import PipelineConfigManager
from ingestion.interfaces import InMemoryDatabaseWriter
from ingestion.models import StandardizedTelemetryModel
from ingestion.pipeline import TelemetryProcessingPipeline
from ingestion.dispatcher import TelemetryEventDispatcher
from ingestion.validator import JsonPayloadValidator
from ingestion.timestamp_validator import ChronoTimestampValidator
from ingestion.duplicate_detector import SlidingWindowDuplicateDetector
from ingestion.quality_checker import OperationalQualityChecker
from ingestion.normalizer import EngineeringUnitNormalizer
from ingestion.metadata_enricher import StaticAssetMetadataEnricher
from ingestion.parser import TelemetryObjectParser
from ingestion.retry_manager import ExponentialBackoffRetryManager


def test_section4_validator():
    validator = JsonPayloadValidator({}, 1048576)
    raw = json.dumps({"test": "data"}).encode("utf-8")
    res = validator.execute_validation(raw)
    assert res["test"] == "data"


def test_section4_chrono_validator():
    chrono = ChronoTimestampValidator(future_limit_sec=5.0, past_limit_sec=86400.0)
    now_iso = datetime.utcnow().isoformat() + "Z"
    chrono.assert_timestamp_bounds({"timestamp": now_iso})


def test_section4_duplicate_detector():
    dedup = SlidingWindowDuplicateDetector(window_sec=60.0, max_elements=50000)
    p = {"sensor_id": "SENS-1", "sequence_number": 500}
    assert dedup.process_deduplication_check(p) is False
    assert dedup.process_deduplication_check(p) is True


def test_section4_quality_checker():
    qc = OperationalQualityChecker({"critical_temperature_upper_bound": 150.0})
    p = {"topic": "gmc/aus/asy/l1/m1/telemetry/TEMPERATURE", "value": 200.0, "quality": "GOOD"}
    score = qc.evaluate_quality_score(p)
    assert score == 50.0


def test_section4_normalizer():
    matrix = {
        "TEMPERATURE": {
            "source_units": {"FAHRENHEIT": "CELSIUS"},
            "conversions": {"FAHRENHEIT": "lambda x: (x - 32) * 5.0 / 9.0"},
            "target_unit": "CELSIUS",
            "output_precision": 2
        }
    }
    norm = EngineeringUnitNormalizer(matrix)
    p = {"topic": "gmc/aus/asy/l1/m1/telemetry/TEMPERATURE", "value": 212.0, "unit": "FAHRENHEIT"}
    norm.normalize_inplace(p)
    assert p["value"] == 100.0
    assert p["unit"] == "CELSIUS"


def test_section4_enricher_and_parser():
    enricher = StaticAssetMetadataEnricher(environment="production", pipeline_version="v4.0")
    p = {
        "timestamp": "2026-07-02T10:00:00Z",
        "asset_id": "ASSET-1",
        "machine_id": "MACH-1",
        "sensor_id": "SENS-1",
        "topic": "gmc/aus/asy/l1/m1/telemetry/TEMP",
        "measurement": "TEMPERATURE",
        "value": 100.0,
        "unit": "CELSIUS",
        "quality": "GOOD",
        "sequence_number": 1,
        "gateway_id": "GW-1",
        "site_id": "SITE-1",
        "plant_id": "PLANT-1",
        "line_id": "LINE-1"
    }
    enricher.enrich_envelope(p, 95.0)
    model = TelemetryObjectParser.map_to_frozen_model(p)
    assert isinstance(model, StandardizedTelemetryModel)
    assert model.quality_score == 95.0
    assert model.pipeline_version == "v4.0"
    assert model.metadata["environment"] == "production"


def test_section4_retry_manager():
    mgr = ExponentialBackoffRetryManager(max_retries=2, base_delay_sec=0.01)
    calls = []
    def op():
        calls.append(1)
        if len(calls) < 2:
            raise ValueError("transient")
        return "success"
    assert mgr.execute_with_retry(op) == "success"


def test_section4_dispatcher_and_pipeline():
    cfg = PipelineConfigManager()
    cfg.parse_all()
    pipeline = TelemetryProcessingPipeline(cfg)
    writer = InMemoryDatabaseWriter()
    dispatcher = TelemetryEventDispatcher(pipeline, writer, pool_workers=2)
    
    dispatcher.start()
    now_iso = datetime.utcnow().isoformat() + "Z"
    p = {
        "timestamp": now_iso,
        "asset_id": "ASSET-99",
        "machine_id": "MACH-99",
        "sensor_id": "SENS-99",
        "topic": "gmc/aus/asy/l1/m1/telemetry/TEMPERATURE",
        "measurement": "TEMPERATURE",
        "value": 212.0,
        "unit": "FAHRENHEIT",
        "quality": "GOOD",
        "sequence_number": 777,
        "gateway_id": "GW-99",
        "site_id": "SITE-AUS",
        "plant_id": "PLANT-GMC",
        "line_id": "LINE-ASY"
    }
    dispatcher.enqueue_raw_packet(json.dumps(p).encode("utf-8"))
    time.sleep(0.4)
    dispatcher.stop()
    assert len(writer.records) == 1
    assert writer.records[0].value == 100.0
    assert writer.records[0].unit == "CELSIUS"
