"""
Multi-device industrial simulator.

Spawns one thread per configured device; each thread loops at its
configured ``update_interval_secs`` and publishes JSON telemetry
payloads to MQTT in the format::

    {
      "device_id": "<id>",
      "timestamp": <epoch_float>,
      "telemetry": {
         "<metric_name>": <float_value>,
         ...
      }
    }

Uses ``paho-mqtt`` v2.x ``CallbackAPIVersion.VERSION2`` API.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

import paho.mqtt.client as mqtt

from .device_profiles import TelemetryGenerator

logger = logging.getLogger("iob.simulator")


class IndustrialSimulator:
    """
    Multi-threaded industrial device simulator.

    Reads ``config["broker"]`` and ``config["devices"]``; for each
    device, launches a daemon thread that emits telemetry at the
    configured cadence until :py:meth:`stop` is called.
    """

    def __init__(self, config: dict):
        self.config = config
        self.broker_cfg = config["broker"]
        self.devices: List[Dict[str, Any]] = config.get("devices", []) or []

        # paho-mqtt v2.x callback API
        self.client = mqtt.Client(
            client_id=self.broker_cfg.get("client_id", "iob_simulator_engine"),
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        username = self.broker_cfg.get("username")
        password = self.broker_cfg.get("password")
        if username:
            self.client.username_pw_set(username, password)

        self.running = False
        self.threads: List[threading.Thread] = []
        self._per_device_step: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Connect to broker and launch one thread per device."""
        self.client.connect(
            self.broker_cfg["host"],
            int(self.broker_cfg["port"]),
            int(self.broker_cfg.get("keepalive", 60)),
        )
        self.client.loop_start()
        self.running = True

        for device_cfg in self.devices:
            t = threading.Thread(
                target=self._device_loop,
                args=(device_cfg,),
                name=f"sim-{device_cfg['id']}",
                daemon=True,
            )
            self._per_device_step[device_cfg["id"]] = 0.0
            self.threads.append(t)
            t.start()
            logger.info(f"Started simulator thread for {device_cfg['id']} "
                        f"(topic={device_cfg['topic']}, "
                        f"interval={device_cfg['update_interval_secs']}s)")

    def stop(self) -> None:
        """Signal threads to stop, then disconnect from broker."""
        self.running = False
        # Give threads a moment to exit their sleep loops
        for t in self.threads:
            t.join(timeout=2.0)
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:  # pragma: no cover - defensive
            pass
        logger.info("Simulator stopped")

    # ------------------------------------------------------------------
    # Per-device loop
    # ------------------------------------------------------------------
    def _device_loop(self, device_cfg: dict) -> None:
        """Publish telemetry for one device in a loop."""
        interval = float(device_cfg.get("update_interval_secs", 1.0))
        # Per-device deterministic RNG (seed by device id for reproducibility)
        rng = TelemetryGenerator.make_deterministic_rng(
            seed=_stable_seed(device_cfg["id"])
        )
        while self.running:
            payload = {
                "device_id": device_cfg["id"],
                "timestamp": time.time(),
                "telemetry": {},
            }
            for metric in device_cfg.get("metrics", []):
                step = self._per_device_step.get(device_cfg["id"], 0.0)
                value = TelemetryGenerator.generate_metric_value(
                    metric, step, rng=rng,
                )
                payload["telemetry"][metric["name"]] = value

            try:
                info = self.client.publish(
                    device_cfg["topic"],
                    json.dumps(payload),
                    qos=1,
                )
                if info.rc != mqtt.MQTT_ERR_SUCCESS:  # pragma: no cover
                    logger.warning(
                        f"MQTT publish rc={info.rc} on {device_cfg['topic']}")
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(f"Publish failed for {device_cfg['id']}: {exc}")

            self._per_device_step[device_cfg["id"]] = (
                self._per_device_step.get(device_cfg["id"], 0.0) + 0.1
            )
            # Sleep but wake promptly when stop() is called
            _interruptible_sleep(interval, lambda: self.running)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _interruptible_sleep(seconds: float, keep_running) -> None:
    """Sleep for ``seconds`` in small slices, exiting early when stop is set."""
    end = time.time() + seconds
    while time.time() < end and keep_running():
        time.sleep(min(0.1, max(0.0, end - time.time())))


def _stable_seed(s: str) -> int:
    """Deterministic hash of a string into a 32-bit int seed."""
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h
