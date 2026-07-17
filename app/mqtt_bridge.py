"""
Asynchronous MQTT Client Bridge — Track A — Stage 2 & Phase 1
Subscribes to Industrial IoT sensor topics and puts them into a shared memory queue.
Features exponential backoff reconnection strategy (up to 60s max wait).
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from gmqtt import Client as MQTTClient
import structlog

from app.core.config import settings

logger = structlog.get_logger("app.services.mqtt_bridge")

# Thread-safe in-memory buffer shared between MQTT and WebSocket
sensor_queue: asyncio.Queue = asyncio.Queue()


class MQTTBridge:
    """
    Asynchronous bridge connecting an external MQTT Broker to our internal
    asyncio.Queue for high-throughput, non-blocking telemetry ingestion.
    """
    def __init__(self) -> None:
        self.host = os.getenv("MQTT_BROKER_HOST", settings.MQTT_BROKER_HOST or "localhost")
        try:
            self.port = int(os.getenv("MQTT_BROKER_PORT", str(settings.MQTT_BROKER_PORT or 1883)))
        except ValueError:
            self.port = 1883
            
        self.keepalive = int(os.getenv("MQTT_KEEPALIVE", str(settings.MQTT_KEEPALIVE or 60)))
        self.client_id = (settings.MQTT_CLIENT_ID or "iob-backend") + "-bridge"
        
        self.client = MQTTClient(self.client_id)
        
        # Register async/sync callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe
        
        # Authentication credentials
        username = os.getenv("MQTT_USERNAME", settings.MQTT_USERNAME)
        password = os.getenv("MQTT_PASSWORD", settings.MQTT_PASSWORD)
        if username:
            self.client.set_auth_credentials(username, password)

        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None

    def on_connect(self, client: MQTTClient, flags: int, rc: int, properties: Any) -> None:
        """Callback invoked when connection to the broker is established."""
        logger.info("Connected to MQTT Broker.", host=self.host, port=self.port, rc=rc)
        self._connected = True
        
        # Subscribe to "industrial/telemetry/#" with Quality of Service (QoS) level 1.
        client.subscribe("industrial/telemetry/#", qos=1)
        logger.info("Subscribed to topic filter: industrial/telemetry/# with QoS 1")

    def on_subscribe(
        self,
        client: MQTTClient,
        mid: int,
        qos: tuple,
        properties: Any,
    ) -> None:
        """
        Callback invoked when the broker acknowledges a subscription.
        """
        logger.info(
            "MQTT subscription acknowledged",
            mid=mid,
            qos=qos,
        )

    def on_message(self, client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any) -> int:
        """
        Callback invoked when a message is received from the MQTT broker.
        Dispatches processing asynchronously to avoid blocking the client loop.
        """
        asyncio.create_task(self.handle_message(topic, payload))
        return 0

    async def handle_message(self, topic: str, payload: bytes) -> None:
        """Parses the telemetry message and pushes it onto the shared queue."""
        try:
            decoded_payload = payload.decode("utf-8")
            json_payload = json.loads(decoded_payload)
            
            message = {
                "topic": topic,
                "payload": json_payload
            }
            
            await sensor_queue.put(message)
            logger.debug("Telemetry message queued", topic=topic, current_size=sensor_queue.qsize())
        except UnicodeDecodeError as exc:
            logger.error("Failed to decode payload as UTF-8", topic=topic, error=str(exc))
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse payload as JSON", topic=topic, error=str(exc))
        except Exception as exc:
            logger.error("Unexpected error handling telemetry message", topic=topic, error=str(exc))

    def on_disconnect(self, client: MQTTClient, packet: Any, exc: Optional[Exception] = None) -> None:
        """Callback invoked when the client disconnects from the broker."""
        logger.warning("Disconnected from MQTT Broker.", error=str(exc) if exc else "Clean disconnect")
        self._connected = False
        if exc is not None:
            self.trigger_reconnect()

    def trigger_reconnect(self) -> None:
        """Spawns a reconnect background task if not already reconnecting."""
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self.reconnect_loop())

    async def reconnect_loop(self) -> None:
        """Background loop trying to re-establish connection to the broker with exponential backoff (up to 60s max)."""
        wait_time = 2
        max_wait = 60
        while not self._connected:
            logger.info(f"Attempting to reconnect to MQTT Broker in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            try:
                await self.client.connect(self.host, self.port, keepalive=self.keepalive)
                break
            except Exception as e:
                logger.error("Reconnection attempt failed", error=str(e), next_retry_s=wait_time)
                wait_time = min(wait_time * 2, max_wait)

    async def start(self) -> None:
        """Starts the MQTT Client and establishes connection to the broker."""
        try:
            logger.info("Connecting to MQTT Broker...", host=self.host, port=self.port)
            await self.client.connect(self.host, self.port, keepalive=self.keepalive)
        except Exception as e:
            logger.error("Failed to connect to MQTT broker during startup", host=self.host, port=self.port, error=str(e))
            self.trigger_reconnect()

    async def stop(self) -> None:
        """Gracefully disconnects and stops the MQTT client."""
        logger.info("Shutting down MQTT Bridge...")
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        try:
            await self.client.disconnect()
        except Exception as e:
            logger.error("Error during MQTT disconnect", error=str(e))


# Global instance
mqtt_bridge_instance = MQTTBridge()
