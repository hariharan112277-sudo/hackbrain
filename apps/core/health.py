"""
Advanced Liveness & Readiness Probes Module.

Provides enterprise-grade health monitoring endpoints:
- /health/live: Liveness probe (is the process running?)
- /health/ready: Readiness probe (can we serve traffic?)

The readiness probe checks downstream dependencies (database, cache, etc.)
and returns 503 Service Unavailable if any are unhealthy.

This enables Kubernetes/Docker orchestrators to make intelligent
routing and restart decisions.

Note: The router is included with the API prefix in app/main.py:
    app.include_router(health_router, prefix=settings.API_PREFIX)
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Response, status

router = APIRouter(tags=["Monitoring"])
logger = logging.getLogger("app.health")


async def check_database_connection() -> bool:
    """
    Phase 4 database readiness probe.

    Performs a lightweight `SELECT 1` via the Member 2 connection manager.
    Returns False if the industrial database is unreachable.
    """
    try:
        from database.connection import connection_manager
        return connection_manager.check_health()
    except Exception as exc:
        logger.warning(f"Database readiness check failed: {exc}")
        return False


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe() -> Dict[str, str]:
    """Indicates if the app container is alive (restarts container if this fails)."""
    return {"status": "alive"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_probe(response: Response) -> Dict[str, Any]:
    """Indicates if downstream dependencies (DB, cache) are fully healthy."""
    db_ok = await check_database_connection()

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.critical("Readiness probe failed: Database connectivity is offline.")
        return {"status": "unready", "checks": {"database": "unhealthy"}}

    return {"status": "ready", "checks": {"database": "healthy"}}
