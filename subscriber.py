"""
MQTT Telemetry Subscriber Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: ISO/IEC 20922 (MQTT 5.0), Asynchronous Decoupled Buffer Push.
"""

import logging
import time
from typing import Any, Optional
try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

from .config import PipelineConfigManager
from .dispatcher import TelemetryEventDispatcher
from .models import RawTelemetryMessage

logger = logging.getLogger("iob.subscriber")


class MqttTelemetrySubscriber:
    """Asynchronous MQTT network transport ingestion boundary interface matching ISA-95 path layouts."""
    def __init__(self, cfg: Optional[PipelineConfigManager] = None, event_dispatcher: Optional[TelemetryEventDispatcher] = None, buffer_queue: Any = None, client_id: str = None):
        if cfg is None:
            cfg = PipelineConfigManager()
            cfg.parse_all()
        self.settings = cfg.topics.get("subscription_registry", {
            "broker_host": "127.0.0.1",
            "broker_port": 1883,
            "client_id": client_id or "iob_pipeline_ingestion_core",
            "keepalive_sec": 60,
            "target_topics": [{"filter": "gmc/aus/asy/+/+/telemetry/+", "qos": 1}]
        })
        if client_id:
            self.settings["client_id"] = client_id

        if buffer_queue is not None and event_dispatcher is None:
            class BufferDispatcher:
                def enqueue_raw_packet(self, raw: Any):
                    if isinstance(raw, RawTelemetryMessage):
                        buffer_queue.put(raw)
                    elif isinstance(raw, dict) and "topic" in raw:
                        buffer_queue.put(RawTelemetryMessage(topic=raw["topic"], payload=raw))
                    else:
                        buffer_queue.put(RawTelemetryMessage(topic="site1/area1/line1/turbine-01/telemetry", payload=raw))
                def start(self): pass
                def stop(self): pass
            self.dispatcher = BufferDispatcher()
        else:
            self.dispatcher = event_dispatcher

        if mqtt:
            try:
                cid = self.settings.get("client_id", "iob_pipeline_ingestion_core")
                if hasattr(mqtt, "CallbackAPIVersion"):
                    self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cid, protocol=mqtt.MQTTv5)
                else:
                    self.client = mqtt.Client(client_id=cid, protocol=mqtt.MQTTv5 if hasattr(mqtt, "MQTTv5") else mqtt.MQTTv311)
            except Exception:
                self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
        else:
            self.client = None

    def _on_connect(self, client, userdata, flags, rc, properties=None) -> None:
        if str(rc) == "0" or rc == 0 or "Success" in str(rc):
            logger.info("Connected to EMQX Broker.")
            for entry in self.settings.get("target_topics", []):
                client.subscribe(entry["filter"], qos=entry.get("qos", 1))
                logger.info(f"Registered topic subscription path: {entry['filter']}")
        else:
            logger.error(f"Inbound network handshake rejected. Reason code: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None) -> None:
        logger.warning(f"Broker connection drop identified (Code: {rc}). Retrying connection loops...")

    def _on_message(self, client, userdata, msg) -> None:
        self.dispatcher.enqueue_raw_packet(msg.payload)

    def push_to_buffer(self, raw: Any) -> None:
        if isinstance(raw, RawTelemetryMessage):
            self.dispatcher.enqueue_raw_packet(raw)
        else:
            self.dispatcher.enqueue_raw_packet(raw)

    def initialize_pipeline(self) -> None:
        if self.dispatcher:
            self.dispatcher.start()
        if self.client:
            try:
                self.client.connect(
                    self.settings.get("broker_host", "127.0.0.1"),
                    self.settings.get("broker_port", 1883),
                    self.settings.get("keepalive_sec", 60)
                )
                self.client.loop_start()
            except Exception as e:
                logger.error(f"Failed connecting to broker: {e}")
        logger.info("Ingestion pipeline layer initialized.")

    def shutdown_pipeline(self) -> None:
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        if self.dispatcher:
            self.dispatcher.stop()
        logger.info("Ingestion pipeline layer safely closed down.")

    def start(self) -> None:
        self.initialize_pipeline()

    def stop(self) -> None:
        self.shutdown_pipeline()
