from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.mqtt_bridge import sensor_queue
from app.deps import decode_token
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

manager = ConnectionManager()

@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    try:
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
        while True:
            if not sensor_queue.empty():
                message = await sensor_queue.get()
                await websocket.send_json(message)
                sensor_queue.task_done()
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info("Client disconnected safely.")
    finally:
        manager.disconnect(websocket)
        logger.info(f"Client connection closed. Active connections: {len(manager.active_connections)}")