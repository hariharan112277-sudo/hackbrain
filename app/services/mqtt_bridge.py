import asyncio
import logging
import json
from gmqtt import Client as MQTTClient

logger = logging.getLogger(__name__)

# Core shared memory buffer bridging MQTT data to FastAPI WebSockets
sensor_queue = asyncio.Queue()

class MQTTBridge:
    def __init__(self, broker_host: str = "localhost", port: int = 1883):
        self.broker_host = broker_host
        self.port = port
        self.client = None

    def on_connect(self, client, flags, rc, properties):
        logger.info("Successfully connected to Industrial MQTT Broker.")
        # Subscribing to all sub-topics under industrial/telemetry/ (e.g., pressure, temp)
        client.subscribe("industrial/telemetry/#", qos=1)

    def on_message(self, client, topic, payload, qos, properties):
        try:
            decoded_payload = json.loads(payload.decode("utf-8"))
            logger.info(f"MQTT Data Received on {topic}: {decoded_payload}")
            
            # Non-blocking injection into the async shared memory queue
            asyncio.create_task(sensor_queue.put({
                "topic": topic,
                "payload": decoded_payload
            }))
        except Exception as e:
            logger.error(f"Failed to process incoming MQTT payload: {e}")

    async def start(self):
        # Unique client ID for the enterprise architecture ecosystem
        self.client = MQTTClient("iob-backend-bridge")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        try:
            await self.client.connect(self.broker_host, self.port)
            logger.info("MQTT Bridge background runner initialized.")
        except Exception as e:
            logger.error(f"Critical: Failed to connect to MQTT Broker: {e}")

# Instantiated single global reference for system consistency
mqtt_bridge = MQTTBridge()