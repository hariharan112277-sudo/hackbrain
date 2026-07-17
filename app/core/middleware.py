"""
Distributed Trace Propagation Middleware
Phase 0 Remediation — Enforces X-Correlation-ID across all inbound requests.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid
import structlog

logger = structlog.get_logger("app.core.middleware")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propagates or injects X-Correlation-ID for distributed trace tracking."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        logger.info(
            "correlation_id_set",
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
        )
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
