"""
Verification Tests for Stage 2: Real-Time Bridge & WebSockets
Tracks both Track A (Asynchronous MQTT Ingestion) and Track B (Authenticated WebSocket Streaming)
"""

import os
import sys

# Direct structural layout path injection to guarantee module execution safety
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket

from app.core.security import create_access_token
from app.services.mqtt_bridge import MQTTBridge, sensor_queue
from app.api.ws import websocket_telemetry_endpoint, manager


# =====================================================================
# 1. WEBSOCKET ENDPOINT & AUTHENTICATION TESTS (DIRECT MOCKING)
# =====================================================================

@pytest.mark.asyncio
async def test_websocket_telemetry_rejection_invalid_token():
    """Verify that a WebSocket connection with an invalid token is rejected with 4001."""
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.client = "127.0.0.1"
    
    await websocket_telemetry_endpoint(mock_ws, token="invalid.token.here")
    
    mock_ws.accept.assert_not_called()
    mock_ws.close.assert_called_once()
    call_kwargs = mock_ws.close.call_args[1]
    assert call_kwargs["code"] == 4001


@pytest.mark.asyncio
async def test_websocket_telemetry_success_and_streaming():
    """Verify successful authentication and data streaming."""
    token = create_access_token({"sub": "user_123", "role": "admin"})
    
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.client = "127.0.0.1"

    # AsyncMock's default return value completes immediately, which would make
    # the endpoint's receive loop spin without yielding. Model a real client
    # that remains connected until the server cancels it.
    async def wait_for_client_message():
        await asyncio.sleep(3600)

    mock_ws.receive_text.side_effect = wait_for_client_message
    task = asyncio.create_task(websocket_telemetry_endpoint(mock_ws, token=token))
    await asyncio.sleep(0.05)

    try:
        mock_ws.accept.assert_called_once()
        assert mock_ws in manager.active_connections

        test_payload = {
            "topic": "industrial/telemetry/temp_sensor_01",
            "payload": {"value": 24.5, "unit": "C"},
        }
        # The production distributor consumes Redis Pub/Sub; the connection
        # manager is the stable unit under test here.
        await manager.broadcast(test_payload)
        mock_ws.send_json.assert_called_with(test_payload)
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert mock_ws not in manager.active_connections


# =====================================================================
# 2. MQTT BRIDGE CLIENT INGESTION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_mqtt_bridge_message_processing():
    """Verify MQTT Bridge processes payloads and passes them to the queue."""
    bridge = MQTTBridge()
    topic = "industrial/telemetry/vibration_sensor_99"
    raw_payload = b'{"velocity": 4.2, "unit": "mm/s"}'
    
    while not sensor_queue.empty():
        sensor_queue.get_nowait()
        
    bridge.on_message(None, topic, raw_payload, 1, None)
    
    for _ in range(10):
        await asyncio.sleep(0.02)
        if not sensor_queue.empty():
            break
            
    assert not sensor_queue.empty()
    queued_msg = await sensor_queue.get()
    
    assert queued_msg["topic"] == topic
    assert queued_msg["payload"]["velocity"] == 4.2


@pytest.mark.asyncio
async def test_mqtt_bridge_subscription_on_connect():
    """Verify that MQTTBridge subscribes to topic filters on connect."""
    bridge = MQTTBridge()
    mock_client = MagicMock()
    
    bridge.on_connect(mock_client, None, 0, None)
    mock_client.subscribe.assert_called_once_with("industrial/telemetry/#", qos=1)