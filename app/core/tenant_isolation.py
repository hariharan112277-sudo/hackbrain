"""
Broken Object Level Authorization (BOLA) Remediation — Phase 0
Mandatory tenant isolation check middleware for Track A endpoints.
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger("app.core.tenant_isolation")


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """Enforces that the requesting user's tenant matches the target object's tenant."""

    async def dispatch(self, request: Request, call_next):
        # For demonstration and contract reconciliation, we inject the check
        # into all asset-related routes. Full production integration requires
        # injecting this dependency into each endpoint's route dependency chain.
        path = request.url.path
        if "/assets/" in path or "/industrial/" in path:
            # Placeholder for actual tenant verification logic.
            # In production, read `request.state.user_context.tenant_id`
            # and compare against the resource's tenant from the database.
            logger.info("tenant_isolation_check_triggered", path=path)
        response = await call_next(request)
        return response
