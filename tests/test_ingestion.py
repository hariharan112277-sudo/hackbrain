"""Tests for ingestion: Pydantic validator + normalization engine + worker."""
import datetime
import json
import time
import unittest
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from src.ingestion.validator import TelemetryPayloadSchema, TelemetryValidator
from src.ingestion.parser import NormalizationEngine
from src.ingestion.mqtt_client import TelemetryIngestionWorker


def _good_payload():
    return {
        "device_id": "DEV_CNC_001",
        "timestamp": time.time(),
        "telemetry": {"spindle_speed_rpm": 8500.0,
                      "vibration_amplitude_g": 1.2},
    }


class TestTelemetryPayloadSchema(unittest.TestCase):
    def test_accepts_valid_payload(self):
        rec = TelemetryPayloadSchema(**_good_payload())
        self.assertEqual(rec.device_id, "DEV_CNC_001")
        self.assertIsInstance(rec.timestamp, float)
        self.assertGreater(len(rec.telemetry), 0)

    def test_rejects_short_device_id(self):
        bad = _good_payload()
        bad["device_id"] = "ab"   # < 3 chars
        with self.assertRaises(ValidationError):
            TelemetryPayloadSchema(**bad)

    def test_rejects_missing_timestamp(self):
        bad = _good_payload()
        del bad["timestamp"]
        with self.assertRaises(ValidationError):
            TelemetryPayloadSchema(**bad)

    def test_rejects_empty_telemetry(self):
        bad = _good_payload()
        bad["telemetry"] = {}
        with self.assertRaises(ValidationError):
            TelemetryPayloadSchema(**bad)

    def test_rejects_non_numeric_metric(self):
        bad = _good_payload()
        bad["telemetry"] = {"spindle": "not_a_number"}
        with self.assertRaises(ValidationError):
            TelemetryPayloadSchema(**bad)


class TestTelemetryValidator(unittest.TestCase):
    def test_validate_payload_returns_schema(self):
        rec = TelemetryValidator.validate_payload(_good_payload())
        self.assertIsInstance(rec, TelemetryPayloadSchema)


class TestNormalizationEngine(unittest.TestCase):
    def test_normalize_builds_uns_record(self):
        rec = TelemetryPayloadSchema(**_good_payload())
        out = NormalizationEngine.normalize(
            rec, "iob/uns/site_alpha/area_machining/cnc001/telemetry"
        )
        self.assertEqual(out["device_id"], "DEV_CNC_001")
        self.assertEqual(out["site_id"], "site_alpha")
        self.assertEqual(out["area_id"], "area_machining")
        self.assertIn("timestamp_utc", out)
        # ISO 8601 with timezone
        parsed = datetime.datetime.fromisoformat(out["timestamp_utc"])
        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(out["metrics"]["spindle_speed_rpm"], 8500.0)

    def test_normalize_handles_short_topic(self):
        rec = TelemetryPayloadSchema(**_good_payload())
        out = NormalizationEngine.normalize(rec, "iob/uns")
        self.assertEqual(out["site_id"], "unknown_site")
        self.assertEqual(out["area_id"], "unknown_area")

    def test_parse_topic_extracts_components(self):
        comp = NormalizationEngine.parse_topic(
            "iob/uns/site_alpha/area_machining/cnc001/telemetry"
        )
        self.assertEqual(comp["site_id"], "site_alpha")
        self.assertEqual(comp["area_id"], "area_machining")
        self.assertEqual(comp["device_id"], "cnc001")
        self.assertEqual(comp["leaf"], "telemetry")


class TestTelemetryIngestionWorker(unittest.TestCase):
    def test_on_message_full_happy_path(self):
        """Worker should: validate -> normalize -> save -> bump stats."""
        repo = MagicMock()
        broker_cfg = {"host": "localhost", "port": 1883, "keepalive": 60}
        worker = TelemetryIngestionWorker(broker_cfg, repo)

        msg = MagicMock()
        msg.topic = "iob/uns/site_alpha/area_machining/cnc001/telemetry"
        msg.payload = json.dumps(_good_payload()).encode("utf-8")

        worker._on_message(None, None, msg)
        repo.save_telemetry.assert_called_once()
        kwargs = repo.save_telemetry.call_args.args[0]
        self.assertEqual(kwargs["device_id"], "DEV_CNC_001")
        self.assertEqual(kwargs["site_id"], "site_alpha")
        self.assertEqual(kwargs["area_id"], "area_machining")
        self.assertEqual(worker.stats["received"], 1)
        self.assertEqual(worker.stats["validated"], 1)
        self.assertEqual(worker.stats["persisted"], 1)
        self.assertEqual(worker.stats["errors"], 0)

    def test_on_message_invalid_json_bumps_errors(self):
        repo = MagicMock()
        worker = TelemetryIngestionWorker(
            {"host": "localhost", "port": 1883, "keepalive": 60}, repo)
        msg = MagicMock()
        msg.topic = "iob/uns/site_alpha/area_machining/cnc001/telemetry"
        msg.payload = b"not json {"
        worker._on_message(None, None, msg)
        self.assertEqual(worker.stats["received"], 1)
        self.assertEqual(worker.stats["errors"], 1)
        repo.save_telemetry.assert_not_called()

    def test_on_message_invalid_schema_bumps_errors(self):
        repo = MagicMock()
        worker = TelemetryIngestionWorker(
            {"host": "localhost", "port": 1883, "keepalive": 60}, repo)
        msg = MagicMock()
        msg.topic = "iob/uns/site_alpha/area_machining/cnc001/telemetry"
        bad = {"device_id": "ab", "timestamp": 0, "telemetry": {}}
        msg.payload = json.dumps(bad).encode("utf-8")
        worker._on_message(None, None, msg)
        self.assertEqual(worker.stats["errors"], 1)
        repo.save_telemetry.assert_not_called()


if __name__ == "__main__":
    unittest.main()
