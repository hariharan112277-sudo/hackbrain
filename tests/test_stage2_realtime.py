"""
Verification Tests for Stage 2: Real-Time Bridge & WebSockets
Tracks both Track A (Asynchronous MQTT Ingestion) and Track B (Authenticated WebSocket Streaming)
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket, WebSocketDisconnect

from app.core.security import create_access_token
from app.services.mqtt_bridge import MQTTBridge, sensor_queue
from app.api.ws import websocket_telemetry, manager, ConnectionManager


# =====================================================================
# 1. WEBSOCKET ENDPOINT & AUTHENTICATION TESTS (DIRECT MOCKING)
# =====================================================================

@pytest.mark.asyncio
async def test_websocket_telemetry_rejection_invalid_token():
    """Verify that a WebSocket connection with an invalid token is rejected with 4001."""
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.client = "127.0.0.1"
    
    # Call endpoint with invalid token
    await websocket_telemetry(mock_ws, token="invalid.token.here")
    
    # Assert websocket was not accepted
    mock_ws.accept.assert_not_called()
    
    # Assert websocket was closed with standard code 4001 (Unauthorized)
    mock_ws.close.assert_called_once()
    call_kwargs = mock_ws.close.call_args[1]
    assert call_kwargs["code"] == 4001
    assert "Unauthorized" in call_kwargs["reason"]


@pytest.mark.asyncio
async def test_websocket_telemetry_success_and_streaming():
    """
    Verify that a WebSocket connection with a valid token:
    1. Successfully authenticates and accepts connection.
    2. Registers the client in the ConnectionManager.
    3. Streams real-time telemetry items from the queue.
    4. Cleans up and unregisters on disconnect.
    """
    token = create_access_token({"sub": "user_123", "role": "admin"})
    
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.client = "127.0.0.1"
    
    # Run the endpoint in a background task so we can interact with it
    task = asyncio.create_task(websocket_telemetry(mock_ws, token=token))
    
    # Wait slightly for the handshake and registration
    await asyncio.sleep(0.05)
    
    try:
        # 1. Assert accept was called
        mock_ws.accept.assert_called_once()
        
        # 2. Assert connection is registered in manager
        assert mock_ws in manager.active_connections
        
        # Get the client queue
        client_queue = manager.active_connections[mock_ws]
        
        # 3. Stream real-time data delivery
        test_payload = {
            "topic": "industrial/telemetry/temp_sensor_01",
            "payload": {"value": 24.5, "unit": "C"}
        }
        await client_queue.put(test_payload)
        
        # Allow the active event loop to poll and send
        await asyncio.sleep(0.15)
        
        # Assert send_json was called with the exact telemetry message
        mock_ws.send_json.assert_called_with(test_payload)
        
    finally:
        # Cancel the background task to simulate disconnect
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        # 4. Assert client is cleanly unregistered from the manager
        assert mock_ws not in manager.active_connections


# =====================================================================
# 2. MQTT BRIDGE CLIENT INGESTION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_mqtt_bridge_message_processing():
    """
    Verify that MQTTBridge.on_message decodes raw bytes payloads,
    constructs the standardized format, and pushes it asynchronously
    onto the shared global sensor_queue.
    """
    bridge = MQTTBridge()
    topic = "industrial/telemetry/vibration_sensor_99"
    raw_payload = b'{"velocity": 4.2, "unit": "mm/s"}'
    
    # Clear queue
    while not sensor_queue.empty():
        sensor_queue.get_nowait()
        
    # Trigger the callback
    bridge.on_message(None, topic, raw_payload, 1, None)
    
    # Allow background event loop to execute the handle_message task
    for _ in range(10):
        await asyncio.sleep(0.02)
        if not sensor_queue.empty():
            break
            
    assert not sensor_queue.empty()
    queued_msg = await sensor_queue.get()
    
    assert queued_msg["topic"] == topic
    assert queued_msg["payload"]["velocity"] == 4.2
    assert queued_msg["payload"]["unit"] == "mm/s"


@pytest.mark.asyncio
async def test_mqtt_bridge_subscription_on_connect():
    """Verify that MQTTBridge subscribes to 'industrial/telemetry/#' on connect."""
    bridge = MQTTBridge()
    mock_client = MagicMock()
    
    bridge.on_connect(mock_client, None, 0, None)
    
    # Assert subscription is set up with QoS 1
    mock_client.subscribe.assert_called_once_with("industrial/telemetry/#", qos=1)
