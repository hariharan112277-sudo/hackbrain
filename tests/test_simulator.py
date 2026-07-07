"""Tests for the simulator (TelemetryGenerator + IndustrialSimulator)."""
import json
import math
import unittest
from unittest.mock import patch, MagicMock

from src.simulator.device_profiles import TelemetryGenerator
from src.simulator.core_simulator import IndustrialSimulator


class TestTelemetryGenerator(unittest.TestCase):
    def test_value_respects_bounds(self):
        cfg = {"min_val": 10.0, "max_val": 100.0, "noise_amplitude": 5.0}
        for _ in range(2000):
            v = TelemetryGenerator.generate_metric_value(cfg, step=0.5)
            self.assertGreaterEqual(v, 10.0)
            self.assertLessEqual(v, 100.0)

    def test_value_changes_over_time(self):
        """Sinusoidal component should cause values to differ across steps."""
        cfg = {"min_val": 0.0, "max_val": 100.0, "noise_amplitude": 0.0}
        v1 = TelemetryGenerator.generate_metric_value(cfg, step=0.0)
        v2 = TelemetryGenerator.generate_metric_value(cfg, step=math.pi)
        # With noise=0, the difference is purely from sin(step*0.125)
        self.assertNotEqual(v1, v2)

    def test_deterministic_with_rng(self):
        cfg = {"min_val": 0.0, "max_val": 100.0, "noise_amplitude": 1.0}
        import random
        a = TelemetryGenerator.generate_metric_value(cfg, 0.0, random.Random(7))
        b = TelemetryGenerator.generate_metric_value(cfg, 0.0, random.Random(7))
        self.assertEqual(a, b)


class TestIndustrialSimulator(unittest.TestCase):
    def _make_config(self):
        return {
            "broker": {
                "host": "localhost",
                "port": 1883,
                "keepalive": 60,
                "client_id": "test_sim",
            },
            "devices": [
                {
                    "id": "TEST_DEV_001",
                    "name": "Test Device",
                    "type": "discrete",
                    "topic": "iob/uns/site_x/area_y/TEST_DEV_001/telemetry",
                    "update_interval_secs": 1.0,
                    "metrics": [
                        {"name": "m1", "data_type": "float",
                         "min_val": 0.0, "max_val": 100.0,
                         "noise_amplitude": 0.5},
                    ],
                }
            ],
        }

    def test_init_does_not_connect(self):
        """Construction must be side-effect-free."""
        sim = IndustrialSimulator(self._make_config())
        self.assertFalse(sim.running)
        self.assertEqual(len(sim.threads), 0)
        self.assertEqual(len(sim.devices), 1)

    @patch("src.simulator.core_simulator.mqtt.Client")
    def test_start_spawns_one_thread_per_device(self, MockClient):
        instance = MagicMock()
        MockClient.return_value = instance

        sim = IndustrialSimulator(self._make_config())
        sim.start()
        try:
            instance.connect.assert_called_once()
            instance.loop_start.assert_called_once()
            self.assertTrue(sim.running)
            self.assertEqual(len(sim.threads), 1)
        finally:
            sim.stop()

    @patch("src.simulator.core_simulator.mqtt.Client")
    def test_publishes_payload_format(self, MockClient):
        instance = MagicMock()
        MockClient.return_value = instance

        sim = IndustrialSimulator(self._make_config())
        # Drive a single tick directly without the infinite loop.
        # We patch the sleep to set running=False on the FIRST call
        # so the loop exits cleanly after one publish.
        sim.running = True

        def _stop_after_first_sleep(_secs, _keep_running):
            sim.running = False

        with patch("src.simulator.core_simulator._interruptible_sleep",
                   side_effect=_stop_after_first_sleep):
            sim._device_loop(sim.devices[0])

        pub_calls = instance.publish.call_args_list
        self.assertGreater(len(pub_calls), 0,
                           "simulator should publish at least one payload")
        topic, payload_str = pub_calls[0].args[0], pub_calls[0].args[1]
        self.assertEqual(topic,
                         "iob/uns/site_x/area_y/TEST_DEV_001/telemetry")
        payload = json.loads(payload_str)
        self.assertIn("device_id", payload)
        self.assertIn("timestamp", payload)
        self.assertIn("telemetry", payload)
        self.assertEqual(payload["device_id"], "TEST_DEV_001")
        self.assertIsInstance(payload["timestamp"], float)
        self.assertIn("m1", payload["telemetry"])


if __name__ == "__main__":
    unittest.main()
