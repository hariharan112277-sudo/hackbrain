"""
Configuration Loader Module for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: YAML / JSON configuration ingestion for OT edge processing.
Section 4 Implementation.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional


class PipelineConfigManager:
    """Loads and encapsulates external YAML/JSON runtime validation matrices."""
    def __init__(self, root_config_dir: str = "config"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(root_config_dir):
            candidate = os.path.join(base_dir, root_config_dir)
            if os.path.exists(candidate):
                self.root = candidate
            elif os.path.exists(root_config_dir):
                self.root = root_config_dir
            else:
                self.root = os.path.join(base_dir, "config")
        else:
            self.root = root_config_dir

        self.rules: Dict[str, Any] = {}
        self.units: Dict[str, Any] = {}
        self.topics: Dict[str, Any] = {}
        self.schema: Dict[str, Any] = {}

    def parse_all(self) -> None:
        rules_path = os.path.join(self.root, "validation_rules.yaml")
        if os.path.exists(rules_path):
            with open(rules_path, "r", encoding="utf-8") as f:
                self.rules = yaml.safe_load(f) or {}

        units_path = os.path.join(self.root, "units.yaml")
        if os.path.exists(units_path):
            with open(units_path, "r", encoding="utf-8") as f:
                self.units = yaml.safe_load(f) or {}

        topics_path = os.path.join(self.root, "topics.yaml")
        if os.path.exists(topics_path):
            with open(topics_path, "r", encoding="utf-8") as f:
                self.topics = yaml.safe_load(f) or {}

        schema_path = os.path.join(self.root, "schema.json")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)

    @property
    def mqtt(self) -> Any:
        class MqttHelper:
            def __init__(self, topics_dict: Dict[str, Any]):
                sr = topics_dict.get("subscription_registry", {})
                self.broker_port = sr.get("broker_port", 1883)
                self.broker_host = sr.get("broker_host", "127.0.0.1")
        return MqttHelper(self.topics)

    @property
    def validation_parameters(self) -> Any:
        class ValHelper:
            def __init__(self, rules_dict: Dict[str, Any]):
                vp = rules_dict.get("validation_parameters", {})
                self.max_payload_size_bytes = vp.get("max_payload_size_bytes", 1048576)
                self.allowed_clock_drift_future_sec = vp.get("allowed_clock_drift_future_sec", 5.0)
                self.allowed_clock_drift_past_sec = vp.get("allowed_clock_drift_past_sec", 86400.0)
        return ValHelper(self.rules)

    @property
    def duplicate_window_seconds(self) -> float:
        return self.rules.get("validation_parameters", {}).get("duplicate_detection_window_sec", 60.0)

    @property
    def units_conversions(self) -> Dict[str, Any]:
        return self.units.get("unit_normalization_matrix", self.units)


# Backwards compatibility helper
class PipelineConfig(PipelineConfigManager):
    @classmethod
    def load_from_dir(cls, config_dir: Optional[str] = None) -> "PipelineConfig":
        mgr = cls(root_config_dir=config_dir or "config")
        mgr.parse_all()
        return mgr
