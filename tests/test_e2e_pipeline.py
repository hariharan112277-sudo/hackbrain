"""
End-to-end pipeline test (no live broker or PG required).

Simulates a full pipeline run with mocked paho-mqtt publisher +
subscriber and a mocked DB connection.  Verifies that data published
by the simulator ends up being inserted into the repository.
"""
import json
import time
import unittest
from unittest.mock import MagicMock, patch

from src.config_loader import ConfigLoader
from src.simulator.core_simulator import IndustrialSimulator
from src.ingestion.mqtt_client import TelemetryIngestionWorker
from src.database.telemetry_repository import TelemetryRepository


class TestE2EPipeline(unittest.TestCase):
    CONFIG = ("config/simulator_config.yaml")

    def test_published_payload_flows_through_to_repository(self):
        """
        1. Load real config.
        2. Run the simulator in a single iteration; capture published payload.
        3. Feed that payload into the worker's _on_message.
        4. Verify the repository's save_telemetry was called with the
           normalized UNS record.
        """
        from pathlib import Path
        cfg_path = Path(__file__).resolve().parent.parent / "config" / "simulator_config.yaml"
        cfg = ConfigLoader.load_yaml(str(cfg_path))

        # Step 2: simulator publishes one payload (single iteration, no live broker)
        # We capture the REAL json bytes written by the simulator via a side_effect
        captured = []
        with patch("src.simulator.core_simulator.mqtt.Client") as MockPub:
            pub_instance = MagicMock()
            # Make publish(rc=...) succeed by returning a real rc=0
            publish_result = MagicMock()
            publish_result.rc = 0  # MQTT_ERR_SUCCESS
            pub_instance.publish.return_value = publish_result
            MockPub.return_value = pub_instance

            def _capture(*args, **kwargs):
                captured.append((args[0], args[1]))
                return publish_result

            pub_instance.publish.side_effect = _capture

            sim = IndustrialSimulator(cfg)
            sim.running = True

            def _stop_after_first_sleep(_secs, _keep_running):
                sim.running = False

            with patch("src.simulator.core_simulator._interruptible_sleep",
                       side_effect=_stop_after_first_sleep):
                sim._device_loop(sim.devices[0])
            self.assertGreater(len(captured), 0,
                               "simulator should publish at least one payload")
            pub_calls = captured  # list of (topic, payload_str)

        # Step 3: feed the first published payload into the ingestion worker
        repo = MagicMock(spec=TelemetryRepository)
        worker = TelemetryIngestionWorker(cfg["broker"], repo)

        msg = MagicMock()
        msg.topic = pub_calls[0][0]
        msg.payload = pub_calls[0][1].encode("utf-8")
        worker._on_message(None, None, msg)

        # Step 4: verify normalized record reached the repo
        self.assertEqual(worker.stats["persisted"], 1)
        repo.save_telemetry.assert_called_once()
        normalized = repo.save_telemetry.call_args.args[0]
        self.assertIn("device_id", normalized)
        self.assertIn("site_id", normalized)
        self.assertIn("area_id", normalized)
        self.assertIn("timestamp_utc", normalized)
        self.assertIn("metrics", normalized)
        self.assertIsInstance(normalized["metrics"], dict)
        self.assertGreater(len(normalized["metrics"]), 0)


if __name__ == "__main__":
    unittest.main()
