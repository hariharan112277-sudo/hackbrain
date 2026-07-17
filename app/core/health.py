"""Low-cost liveness and dependency readiness probes."""
from __future__ import annotations
import time
from typing import Any, Dict
from fastapi import APIRouter, Response, status
from app.core.config import settings
router = APIRouter(tags=["Monitoring"])

async def check_database_connection() -> bool:
    try:
        from app.core.database.engine import verify_database_connection
        return await verify_database_connection(max_retries=1, retry_interval=0.05, timeout=2.0)
    except Exception:
        return False

def _mqtt_connected() -> bool:
    try:
        from app.services.mqtt_bridge import mqtt_bridge_instance
        return bool(mqtt_bridge_instance.connected)
    except Exception:
        return False

@router.get("/live")
async def liveness_probe() -> Dict[str, str]:
    # Keep the established public contract; HTTP 200 is the probe signal.
    return {"status": "alive"}

@router.get("/ready")
async def readiness_probe(response: Response) -> Dict[str, Any]:
    started = time.perf_counter()
    db_ok = await check_database_connection()
    mqtt_ok = _mqtt_connected()
    checks = {"database": "healthy" if db_ok else "unhealthy", "mqtt": "healthy" if mqtt_ok else "degraded"}
    # MQTT is allowed to be unavailable in development; production readiness
    # still requires the database and reports the edge link explicitly.
    ready = db_ok and (mqtt_ok or not settings.is_production)
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if ready else "not_ready", "checks": checks, "latency_ms": round((time.perf_counter()-started)*1000, 2)}
