import asyncio
import json
import logging
import time
from typing import List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.config import settings
from app.deps import decode_token
from shared.event_bus import redis_pool, subscribe_channel

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send message to all active connections."""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()
_distributor_task: Optional[asyncio.Task] = None

async def _distribute_telemetry():
    """Background task to pull telemetry from Redis and broadcast to WebSockets.

    Phase 4 (R-4.6.1): When ``settings.WS_BROADCAST_BATCH_MS`` is greater than
    zero, individual telemetry events are grouped into small periodic batches
    (``{"type": "telemetry_batch", "events": [...]}``) to reduce the processing
    burden on slow client applications. The default of 0 preserves the legacy
    per-message broadcast behaviour for full backwards compatibility.
    """
    logger.info("Starting WebSocket telemetry distributor...")
    pubsub = await subscribe_channel("pubsub:telemetry")

    batch_window_s = max(0, int(getattr(settings, "WS_BROADCAST_BATCH_MS", 0))) / 1000.0
    batch_max = max(1, int(getattr(settings, "WS_BROADCAST_BATCH_MAX", 50)))
    batch: List[dict] = []
    batch_started_at = time.monotonic()

    async def _flush_batch():
        nonlocal batch, batch_started_at
        if not batch:
            return
        if len(batch) == 1:
            await manager.broadcast(batch[0])
        else:
            await manager.broadcast({"type": "telemetry_batch", "count": len(batch), "events": batch})
        batch = []
        batch_started_at = time.monotonic()

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                payload = json.loads(message["data"])
                if batch_window_s <= 0:
                    # Legacy immediate broadcast path
                    await manager.broadcast(payload)
                    continue
                batch.append(payload)
                elapsed = time.monotonic() - batch_started_at
                if len(batch) >= batch_max or elapsed >= batch_window_s:
                    await _flush_batch()
            except Exception as e:
                logger.error(f"Distributor payload error: {e}")
    except asyncio.CancelledError:
        logger.info("WebSocket telemetry distributor task cancelled.")
        try:
            await _flush_batch()
        except Exception:
            pass
    finally:
        await pubsub.unsubscribe("pubsub:telemetry")

def start_distributor():
    """Start the global telemetry distributor."""
    global _distributor_task
    if _distributor_task is None or _distributor_task.done():
        _distributor_task = asyncio.create_task(_distribute_telemetry())

async def stop_distributor():
    """Stop the global telemetry distributor."""
    global _distributor_task
    if _distributor_task:
        _distributor_task.cancel()
        try:
            await _distributor_task
        except asyncio.CancelledError:
            pass
        _distributor_task = None

@router.websocket("/stream")
async def websocket_telemetry_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    try:
        # Phase 2: Enforce authorization during initial connection upgrade
        user = decode_token(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid authentication token")
            return
    except Exception as e:
        logger.error(f"WebSocket Handshake Authentication Failure: {e}")
        await websocket.close(code=4001, reason="Authentication execution failed")
        return

    await manager.connect(websocket)
    logger.info(f"Secure client channel initialized. Active connections: {len(manager.active_connections)}")

    try:
        # Keep connection open. Broadcasting is handled by the distributor.
        while True:
            # Phase 4 (Section 6): Application-level heartbeat support.
            # Clients may send {"type": "ping"} (or the literal "ping") and
            # receive a pong echo so latency profiles can be monitored.
            text = await websocket.receive_text()
            try:
                if text == "ping":
                    await websocket.send_json({"type": "pong"})
                elif isinstance(text, str) and text.startswith("{"):
                    msg = json.loads(text)
                    if isinstance(msg, dict) and msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong", "ts": msg.get("ts")})
            except (json.JSONDecodeError, TypeError):
                # Non-JSON client chatter is ignored; channel is broadcast-only.
                pass
    except WebSocketDisconnect:
        logger.info("Client disconnected safely.")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)
        logger.info(f"Client connection closed. Active connections: {len(manager.active_connections)}")
