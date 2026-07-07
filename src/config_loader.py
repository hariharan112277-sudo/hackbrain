"""
Configuration loader for the IOB Data Engine - Stage 1.

Loads the YAML configuration file (``config/simulator_config.yaml``) and
exposes it as a plain ``dict``.  This matches the simpler spec used by
the rest of Stage 1 (no Pydantic validation at config layer — that
happens at the telemetry ingestion boundary).

Also provides a small legacy-config merge helper so that if this
package is dropped into the existing repo (which already has
``config/machines.yaml`` + ``config/sensors.yaml``), those devices can
be transparently appended.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger("iob.config_loader")


class ConfigLoader:
    """
    Loads YAML config from disk and returns a plain ``dict``.

    Usage::

        config = ConfigLoader.load_yaml("config/simulator_config.yaml")
        broker_cfg = config["broker"]
        devices    = config["devices"]
    """

    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """Read a YAML file and return its parsed contents."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(
                f"Config root must be a mapping, got {type(data).__name__} "
                f"in {file_path}"
            )
        # Light-touch validation
        if "broker" not in data:
            raise ValueError("Config is missing required 'broker' section")
        if "devices" not in data or not isinstance(data["devices"], list):
            raise ValueError("Config is missing required 'devices' list")
        for i, dev in enumerate(data["devices"]):
            if "id" not in dev or "topic" not in dev or "metrics" not in dev:
                raise ValueError(
                    f"Device #{i} missing required keys (id, topic, metrics): "
                    f"{dev}"
                )
        logger.info(f"Loaded config from {file_path} "
                    f"(version={data.get('version', '?')}, "
                    f"devices={len(data['devices'])})")
        return data

    @staticmethod
    def load_with_legacy(
        file_path: str,
        legacy_devices_path: Optional[str] = None,
        legacy_sensors_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Load the Stage 1 config and (optionally) merge in additional
        devices from legacy ``machines.yaml`` / ``sensors.yaml`` files
        (used when integrating with the existing repo).
        """
        cfg = ConfigLoader.load_yaml(file_path)
        if legacy_devices_path and Path(legacy_devices_path).exists():
            try:
                legacy = yaml.safe_load(Path(legacy_devices_path).read_text(
                    encoding="utf-8")) or {}
                existing_ids = {d["id"] for d in cfg["devices"]}
                machines = legacy.get("machines", legacy.get("devices", []))
                if isinstance(machines, list):
                    added = 0
                    for m in machines:
                        if isinstance(m, dict) and m.get("id") \
                                and m["id"] not in existing_ids:
                            cfg["devices"].append(_translate_legacy_device(m))
                            existing_ids.add(m["id"])
                            added += 1
                    if added:
                        logger.info(
                            f"Legacy config merge: +{added} devices from "
                            f"{legacy_devices_path}"
                        )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"Legacy config merge failed: {exc}")
        return cfg


def _translate_legacy_device(m: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate a legacy ``machines.yaml`` device entry into the Stage 1
    YAML device schema.  The legacy format may use different keys
    (``device_id`` instead of ``id``, etc.).
    """
    device_id = m.get("id") or m.get("device_id") or m.get("machine_id", "?")
    topic = m.get("topic") or (
        f"iob/uns/{m.get('site', 'site_unknown')}/"
        f"{m.get('area', 'area_unknown')}/{device_id}/telemetry"
    )
    metrics = []
    for s in (m.get("metrics") or m.get("sensors") or []):
        if isinstance(s, str):
            metrics.append({
                "name": s,
                "data_type": "float",
                "min_val": 0.0,
                "max_val": 100.0,
                "noise_amplitude": 0.0,
            })
        elif isinstance(s, dict):
            metrics.append({
                "name": s.get("name", s.get("sensor_id", s.get("id", "m"))),
                "data_type": s.get("data_type", "float"),
                "min_val": float(s.get("min_val", s.get("min", 0.0))),
                "max_val": float(s.get("max_val", s.get("max", 100.0))),
                "noise_amplitude": float(s.get("noise_amplitude", 0.0)),
            })
    return {
        "id": device_id,
        "name": m.get("name", m.get("device_type", device_id)),
        "type": m.get("type", m.get("profile", "continuous")),
        "topic": topic,
        "update_interval_secs": float(m.get("update_interval_secs", 1.0)),
        "metrics": metrics,
    }
