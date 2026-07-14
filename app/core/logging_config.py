"""
Structured Logging Configuration
Phase 5: Production-grade structured logging with structlog.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggingMiddleware:
    """ASGI middleware for request/response logging."""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("app.middleware.logging")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = scope.get("headers", {}).get(b"x-request-id", b"").decode()
        
        # Log request
        self.logger.info(
            "http_request_started",
            method=scope["method"],
            path=scope["path"],
            query_string=scope.get("query_string", b"").decode(),
            request_id=request_id,
        )

        # Wrap send to capture response
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            self.logger.error(
                "http_request_failed",
                method=scope["method"],
                path=scope["path"],
                error=str(e),
                request_id=request_id,
                exc_info=True,
            )
            raise
        else:
            self.logger.info(
                "http_request_completed",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code,
                request_id=request_id,
            )