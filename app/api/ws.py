"""
Authenticated WebSocket Endpoint — Track B (Lathika) — Stage 2
Real-Time Telemetry Streaming & Connection Management
"""

import asyncio
from typing import Dict, Any, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
import structlog

from app.services.mqtt_bridge import sensor_queue

logger = structlog.get_logger("app.api.ws")

router = APIRouter()

# =====================================================================
# CONNECTION MANAGER (Global Registry)
# =====================================================================

class ConnectionManager:
    """
    Manages active WebSocket connections and their associated client-specific
    queues to prevent consumer contention on the single shared sensor_queue.
    """
    def __init__(self) -> None:
        # Maps WebSocket connection to its dedicated asyncio.Queue
        self.active_connections: Dict[WebSocket, asyncio.Queue] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts and registers a new authenticated WebSocket connection."""
        await websocket.accept()
        self.active_connections[websocket] = asyncio.Queue()
        logger.info("WebSocket connection established", client=websocket.client)

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregisters a WebSocket connection cleanly."""
        self.active_connections.pop(websocket, None)
        logger.info("WebSocket connection closed", client=websocket.client)

    async def distribute_to_all(self, message: Dict[str, Any]) -> None:
        """Pushes a message onto all active client queues."""
        for client_queue in self.active_connections.values():
            try:
                client_queue.put_nowait(message)
            except Exception as e:
                logger.error("Failed to push message to client queue", error=str(e))


manager = ConnectionManager()

# =====================================================================
# SENSOR QUEUE DISTRIBUTOR (Background Loop)
# =====================================================================

_distributor_task: Optional[asyncio.Task] = None

async def _distribute_loop() -> None:
    """
    Background worker loop that continuously drains the global sensor_queue
    and broadcasts incoming telemetry items to all active connection queues.
    """
    logger.info("Starting sensor queue distributor loop...")
    while True:
        try:
            # Poll the shared MQTT telemetry queue
            message = await sensor_queue.get()
            # Distribute message to all connected clients
            await manager.distribute_to_all(message)
            sensor_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Sensor queue distributor loop cancelled.")
            break
        except Exception as e:
            logger.error("Error in sensor queue distributor loop", error=str(e))
            await asyncio.sleep(1)


def start_distributor() -> asyncio.Task:
    """Spawns the background queue distributor task."""
    global _distributor_task
    if _distributor_task is None or _distributor_task.done():
        _distributor_task = asyncio.create_task(_distribute_loop())
    return _distributor_task


async def stop_distributor() -> None:
    """Cancels and cleans up the background distributor task."""
    global _distributor_task
    if _distributor_task is not None:
        _distributor_task.cancel()
        try:
            await _distributor_task
        except asyncio.CancelledError:
            pass
        _distributor_task = None


# =====================================================================
# AUTHENTICATED WEBSOCKET ENDPOINT
# =====================================================================

@router.websocket("/ws/telemetry")
async def websocket_telemetry(
    websocket: WebSocket,
    token: str = Query(...)
) -> None:
    """
    FastAPI WebSocket endpoint for streaming real-time industrial telemetry.
    
    1. Authenticates the client using app.deps.decode_token before accepting.
    2. Rejects invalid connections with status code 4001.
    3. Streams telemetry messages in real-time from the backend's sensor_queue.
    """
    # ── Authentication Handshake ──────────────────────────────────────
    try:
        from app.deps import decode_token
        # Invoke app.deps.decode_token to validate the connection
        decode_token(token)
    except Exception as exc:
        # If the token is expired, invalid, or missing, immediately close the socket connection
        # with the standard code 4001 (Unauthorized) and a clean descriptive reason message.
        # Do NOT run websocket.accept().
        reason = "Unauthorized: Invalid or expired token"
        if hasattr(exc, "detail"):
            reason = f"Unauthorized: {exc.detail}"
        elif hasattr(exc, "message"):
            reason = f"Unauthorized: {exc.message}"
            
        logger.warning("WebSocket handshake rejected", client=websocket.client, reason=reason)
        await websocket.close(code=4001, reason=reason)
        return

    # ── Connection Registration ───────────────────────────────────────
    await manager.connect(websocket)
    client_queue = manager.active_connections[websocket]

    # ── Real-Time Streaming Loop ──────────────────────────────────────
    try:
        while True:
            # Poll client queue for new messages from sensor_queue
            if not client_queue.empty():
                message = await client_queue.get()
                await websocket.send_json(message)
                client_queue.task_done()
                
            # Ensure an explicit non-blocking sleep is run to prevent thread starvation
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally", client=websocket.client)
    except Exception as e:
        logger.error("WebSocket connection encountered an error", client=websocket.client, error=str(e))
    finally:
        # Cleanly unregister clients from the manager
        manager.disconnect(websocket)
