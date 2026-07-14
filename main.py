"""
Member 1 - IoT Core API Backend (Root Entry Point).

This module serves as the backward-compatible root entry point.
It delegates to the enterprise application factory in app.main
while preserving the legacy telemetry endpoints for existing consumers.

For the full application factory, see app.main.create_app().
"""
from fastapi import FastAPI

# Import the enterprise application factory
from app.main import create_app

# Create the root-level app instance (delegates to factory)
app = create_app()

# Import legacy telemetry endpoints for backward compatibility
import subprocess
import json
import logging

from app.core.config import settings

logger = logging.getLogger("app.legacy")


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint — basic service status."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/telemetry/latest", tags=["Telemetry"])
def get_latest_telemetry(limit: int = 10):
    """Retrieve latest telemetry records from the database."""
    sql = (
        f"SELECT json_build_object('id', id, 'timestamp', timestamp, "
        f"'machine_id', machine_id, 'measured_value', measured_value) "
        f"FROM industrial.telemetry ORDER BY timestamp DESC LIMIT {limit};"
    )
    cmd = [
        "docker", "exec", "-i", "iob_postgres_db",
        "psql", "-U", "postgres", "-d", "iob", "-t", "-c", sql,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        rows = [json.loads(line.strip()) for line in result.stdout.splitlines() if line.strip()]
        return {"success": True, "data": rows}
    return {"success": False, "error": result.stderr.strip()}


@app.get("/api/telemetry/machine/{machine_id}/history", tags=["Telemetry"])
def get_machine_history(machine_id: str, limit: int = 50):
    """Retrieve time-series telemetry for a specific machine (for Member 3 AI Engine)."""
    sql = (
        f"SELECT json_build_object('id', id, 'timestamp', timestamp, "
        f"'machine_id', machine_id, 'measured_value', measured_value) "
        f"FROM industrial.telemetry WHERE machine_id = '{machine_id}' "
        f"ORDER BY timestamp DESC LIMIT {limit};"
    )
    cmd = [
        "docker", "exec", "-i", "iob_postgres_db",
        "psql", "-U", "postgres", "-d", "iob", "-t", "-c", sql,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        rows = [json.loads(line.strip()) for line in result.stdout.splitlines() if line.strip()]
        return {"success": True, "data": rows}
    return {"success": False, "error": result.stderr.strip()}


# Entry point for direct execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
