"""
MQTT ingestion worker.

Subscribes to ``iob/uns/#`` (the full Unified Namespace tree), validates
each incoming payload with the Pydantic schema, normalizes it via
``NormalizationEngine``, and persists to PostgreSQL via
``TelemetryRepository``.

Uses ``paho-mqtt`` v2.x with ``CallbackAPIVersion.VERSION2``.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

import paho.mqtt.client as mqtt

from .validator import TelemetryValidator
from .parser import NormalizationEngine
from ..database.telemetry_repository import TelemetryRepository

logger = logging.getLogger("iob.ingestion.mqtt")


class TelemetryIngestionWorker:
    """
    MQTT subscriber that drives the Stage 1 ingestion pipeline.

    Wiring::

        broker -> MQTT topic -> JSON -> TelemetryValidator
                                          -> NormalizationEngine
                                          -> TelemetryRepository (PG INSERT)
    """

    def __init__(self, broker_cfg: Dict[str, Any], repo: TelemetryRepository):
        self.broker_cfg = broker_cfg
        self.repo = repo
        self.stats = {
            "received": 0,
            "validated": 0,
            "persisted": 0,
            "errors": 0,
        }
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        username = broker_cfg.get("username")
        password = broker_cfg.get("password")
        if username:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._connected = False

    # ------------------------------------------------------------------
    # paho callbacks
    # ------------------------------------------------------------------
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self._connected = True
            client.subscribe("iob/uns/#", qos=1)
            logger.info("Ingestion worker connected; subscribed to iob/uns/#")
        else:
            logger.error(f"Ingestion worker MQTT connect failed rc={rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self._connected = False
        logger.warning(f"Ingestion worker disconnected rc={rc}")

    def _on_message(self, client, userdata, msg):
        """Validate -> Normalize -> Persist.  Errors logged, never raised."""
        self.stats["received"] += 1
        try:
            raw_payload = json.loads(msg.payload.decode("utf-8"))
            validated = TelemetryValidator.validate_payload(raw_payload)
            normalized = NormalizationEngine.normalize(validated, msg.topic)
            self.repo.save_telemetry(normalized)
            self.stats["validated"] += 1
            self.stats["persisted"] += 1
        except json.JSONDecodeError as exc:
            self.stats["errors"] += 1
            logger.warning(
                f"[INGESTION ERROR] Bad JSON on {msg.topic}: {exc}")
        except Exception as exc:
            self.stats["errors"] += 1
            logger.warning(
                f"[INGESTION ERROR] Failed to process telemetry packet on "
                f"topic {msg.topic}: {exc}"
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Connect to broker and start the network loop in a background thread."""
        self.client.connect(
            self.broker_cfg["host"],
            int(self.broker_cfg["port"]),
            int(self.broker_cfg.get("keepalive", 60)),
        )
        self.client.loop_start()
        logger.info(f"Ingestion worker started "
                    f"({self.broker_cfg['host']}:{self.broker_cfg['port']})")

    def stop(self) -> None:
        """Stop network loop and disconnect."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:  # pragma: no cover
            pass
        logger.info(f"Ingestion worker stopped; stats={self.stats}")

    @property
    def connected(self) -> bool:
        return self._connected
