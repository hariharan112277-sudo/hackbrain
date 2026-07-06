"""
IOB Phase 3 - Configuration Manager

Loads and validates the declarative YAML configuration that drives the
simulation. This is the single entry point the orchestrator uses to read
factory metadata, machine definitions, sensor templates and MQTT settings.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("iob.config")

REQUIRED_MACHINE_KEYS = ("machine_id", "name", "type", "manufacturer", "production_line")
REQUIRED_SENSOR_KEYS = (
    "sensor_sub_id",
    "name",
    "type",
    "min_range",
    "max_range",
    "unit",
    "frequency_hz",
    "noise_variance",
    "failure_probability",
)


class ConfigError(Exception):
    """Raised when the declarative configuration is missing or invalid."""


class ConfigManager:
    """
    Loads and validates the declarative YAML configuration set.

    Resolution order for the configuration directory:
      1. ``config_dir`` argument
      2. ``IOB_CONFIG_DIR`` environment variable
      3. ``<project_root>/config`` (default, robust to the current working dir)
    """

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = os.environ.get("IOB_CONFIG_DIR")
        if config_dir is None:
            # simulator/config.py -> project_root/config
            config_dir = str(Path(__file__).resolve().parent.parent / "config")

        self.config_dir = Path(config_dir)

        machines_doc = self._require("machines.yaml")
        self.factory_metadata: Dict[str, str] = machines_doc["factory_metadata"]
        self.machines: List[Dict[str, Any]] = machines_doc["machines"]

        sensors_doc = self._require("sensors.yaml")
        self.sensor_templates: Dict[str, List[Dict[str, Any]]] = sensors_doc["sensor_templates"]

        topics_doc = self._require("topics.yaml")
        self.mqtt_settings: Dict[str, Any] = topics_doc["mqtt_settings"]

        self._validate()

    # -- loading -----------------------------------------------------------
    def _require(self, name: str) -> Dict[str, Any]:
        path = self.config_dir / name
        if not path.exists():
            raise ConfigError(f"Missing required configuration file: {path}")
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Failed to parse {name}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"Configuration file {name} did not parse to a mapping.")
        return data

    # -- validation --------------------------------------------------------
    def _validate(self) -> None:
        if not self.machines:
            raise ConfigError("No machines defined in machines.yaml")

        for machine in self.machines:
            missing = [k for k in REQUIRED_MACHINE_KEYS if k not in machine]
            if missing:
                raise ConfigError(
                    f"Machine {machine.get('machine_id', '?')} missing required keys: {missing}"
                )
            if machine["type"] not in self.sensor_templates:
                logger.warning(
                    f"No sensor templates for machine type '{machine['type']}' "
                    f"(machine {machine['machine_id']}); it will expose no sensors."
                )

        for mtype, templates in self.sensor_templates.items():
            for template in templates:
                missing = [k for k in REQUIRED_SENSOR_KEYS if k not in template]
                if missing:
                    raise ConfigError(
                        f"Sensor template for '{mtype}' missing required keys: {missing}"
                    )
                if float(template["min_range"]) > float(template["max_range"]):
                    raise ConfigError(
                        f"Sensor template {template.get('sensor_sub_id')} has "
                        f"min_range > max_range."
                    )

    # -- convenience accessors --------------------------------------------
    @property
    def enterprise(self) -> str:
        return self.factory_metadata["enterprise"]

    @property
    def site(self) -> str:
        return self.factory_metadata["site"]

    @property
    def plant(self) -> str:
        return self.factory_metadata["plant"]

    def root_namespace(self) -> str:
        return self.mqtt_settings.get(
            "root_namespace",
            f"{self.enterprise}/{self.site}/{self.plant}".lower(),
        )
