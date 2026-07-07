"""Tests for the YAML config loader."""
import unittest
from pathlib import Path

from src.config_loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    DEFAULT = Path(__file__).resolve().parent.parent / "config" / "simulator_config.yaml"

    def test_loads_default_yaml(self):
        cfg = ConfigLoader.load_yaml(str(self.DEFAULT))
        self.assertEqual(cfg["version"], "1.0")
        self.assertEqual(cfg["broker"]["port"], 1883)
        self.assertGreater(len(cfg["devices"]), 0)

    def test_required_sections_present(self):
        cfg = ConfigLoader.load_yaml(str(self.DEFAULT))
        self.assertIn("broker", cfg)
        self.assertIn("devices", cfg)
        for d in cfg["devices"]:
            self.assertIn("id", d)
            self.assertIn("topic", d)
            self.assertIn("metrics", d)
            for m in d["metrics"]:
                self.assertIn("name", m)
                self.assertIn("min_val", m)
                self.assertIn("max_val", m)

    def test_missing_broker_raises(self):
        import yaml
        bad = Path(self.DEFAULT).parent / "_bad_cfg.yaml"
        bad.write_text("version: '1.0'\ndevices: []\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                ConfigLoader.load_yaml(str(bad))
        finally:
            bad.unlink()

    def test_missing_devices_raises(self):
        import yaml
        bad = Path(self.DEFAULT).parent / "_bad_cfg2.yaml"
        bad.write_text("version: '1.0'\nbroker: {host: x, port: 1}\n",
                       encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                ConfigLoader.load_yaml(str(bad))
        finally:
            bad.unlink()

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            ConfigLoader.load_yaml("/tmp/does_not_exist_xyz.yaml")


if __name__ == "__main__":
    unittest.main()
