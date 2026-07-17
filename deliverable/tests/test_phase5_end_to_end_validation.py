"""Phase 5 regression tests for the cross-boundary contracts.

These tests deliberately use in-process doubles for Redis/MQTT so they run in
CI without requiring Docker, while exercising the real application wiring.
"""
from unittest.mock import AsyncMock

import pytest

from app.services.mqtt_bridge import MQTTBridge, sensor_queue


@pytest.mark.asyncio
async def test_telemetry_is_retained_when_redis_is_unavailable(monkeypatch):
    while not sensor_queue.empty():
        sensor_queue.get_nowait()

    publish = AsyncMock(side_effect=ConnectionError("redis offline"))
    monkeypatch.setattr("shared.event_bus.publish_telemetry", publish)

    bridge = MQTTBridge()
    bridge.on_message(None, "industrial/telemetry/press-01", b'{"value": 7.2}', 1, None)
    await __import__("asyncio").sleep(0)
    message = await sensor_queue.get()

    assert message["topic"] == "industrial/telemetry/press-01"
    assert message["payload"] == {"value": 7.2}
    publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_malformed_telemetry_does_not_reach_queue():
    while not sensor_queue.empty():
        sensor_queue.get_nowait()
    bridge = MQTTBridge()
    bridge.on_message(None, "industrial/telemetry/bad", b"not-json", 1, None)
    await __import__("asyncio").sleep(0)
    assert sensor_queue.empty()
