"""
IOB Phase 3 - MQTT Publisher Engine

Managed connection engine interfacing with the physical EMQX message bus.
Degrades gracefully to OFFLINE mode when paho-mqtt is unavailable or the
broker cannot be reached, so the simulation core keeps producing telemetry.
"""

import json
import logging
import os
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("iob.mqtt")

try:  # paho-mqtt is an optional runtime dependency
    import paho.mqtt.client as mqtt

    _PAHO_AVAILABLE = True
except Exception:  # pragma: no cover - environment without paho
    mqtt = None  # type: ignore
    _PAHO_AVAILABLE = False


class MqttPublisherEngine:
    """
    Managed asynchronous connection engine interfacing with the physical
    EMQX message bus.
    """

    def __init__(
        self,
        settings: Dict[str, Any],
        sink: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.host: str = settings["broker_host"]
        self.port: int = int(settings["broker_port"])
        self.client_id: str = settings["client_id"]
        self.keepalive: int = int(settings.get("keepalive_sec", 60))

        # Optional callable invoked for every dispatched payload. Useful for
        # local logging and for tests that need to capture outbound telemetry
        # without a live broker.
        self.sink = sink
        self._log_offline = os.environ.get("IOB_LOG_OFFLINE", "").lower() in ("1", "true", "yes")

        self.connected: bool = False
        self.client = None

        if not _PAHO_AVAILABLE:
            logger.warning("paho-mqtt not installed; running in OFFLINE mode (no broker).")
            return

        try:  # paho-mqtt >= 2.0 requires a callback API version
            from paho.mqtt.client import CallbackAPIVersion

            self.client = mqtt.Client(
                client_id=self.client_id,
                protocol=mqtt.MQTTv5,
                callback_api_version=CallbackAPIVersion.VERSION2,
            )
        except Exception:  # pragma: no cover - paho-mqtt < 2.0
            self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv5)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    # -- callbacks ---------------------------------------------------------
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        # ``rc`` is an int on paho 1.x and a ReasonCode on paho 2.x.
        try:
            ok = rc == 0 if isinstance(rc, int) else bool(getattr(rc, "is_success", True))
        except Exception:
            ok = True
        if ok:
            self.connected = True
            logger.info("Successfully bound to external industrial network interface core broker.")
        else:
            self.connected = False
            logger.error(f"Inbound network handshake rejected. Return Code: {rc}")

    def _on_disconnect(self, client, userdata, *args):
        self.connected = False
        rc = args[-1] if args else None
        logger.warning(f"Broker connection drop identified. Executing background re-registration routines. Code: {rc}")

    # -- lifecycle ---------------------------------------------------------
    def start(self):
        """Spawns processing loops in an independent background execution context."""
        if self.client is None:
            logger.warning("No MQTT client available; operating in OFFLINE mode.")
            return
        try:
            self.client.connect(self.host, self.port, self.keepalive)
            self.client.loop_start()
        except Exception as ex:
            logger.critical(f"Fatal pipeline extraction socket interface block: {str(ex)}")

    def stop(self):
        """Gracefully tears down network processing loops."""
        if self.client is None:
            return
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    def send(self, topic: str, payload: Dict[str, Any], qos: int = 0):
        """Dispatches serialization strings out through active broker interfaces."""
        if self.client is not None and self.connected:
            try:
                serialized_data = json.dumps(payload)
                self.client.publish(topic, serialized_data, qos=qos, retain=False)
            except Exception as ex:
                logger.error(f"Failed to transmit data payload over network interface: {str(ex)}")

        # Side-channel delivery (capture / offline console logging)
        if self.sink is not None:
            try:
                self.sink(topic, payload)
            except Exception:
                pass
        elif (self.client is None or not self.connected) and self._log_offline:
            logger.info(
                f"[OFFLINE] {topic} -> {payload.get('value')} {payload.get('unit')} "
                f"[{payload.get('quality')}]"
            )
