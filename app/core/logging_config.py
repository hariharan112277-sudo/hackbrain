"""
Structured Logging & Correlation Middleware Module.

This module provides:
1. A thread-safe ContextVar-based correlation ID system that propagates
   the X-Correlation-ID header across the entire request lifecycle.
2. A StructuredJSONFormatter that outputs machine-readable JSON logs with
   full request context (correlation ID, module, function, line, extras).
3. A CorrelationAndLoggingMiddleware that auto-injects correlation IDs,
   measures request duration, and logs structured request/response metrics.
4. A setup_structured_logging() function to configure the root logger.

It is designed to replace the existing integration.logger module while
remaining fully backward-compatible with code that imports
``get_integration_logger`` from ``integration.logger``.
"""
import contextvars
import json
import logging
import sys
import time
from typing import Any
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Thread-safe ContextVar to store the current correlation ID
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured, machine-readable JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S")
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "correlation_id": correlation_id_ctx.get(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra payload fields if they exist
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)  # type: ignore

        return json.dumps(log_data)


def setup_structured_logging(log_level: str, json_format: bool = True) -> None:
    """
    Configures root and application loggers to output structured logs.

    Args:
        log_level: The minimum severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: If True, output structured JSON. If False, use plain text
                     (useful for local development).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove default handlers to prevent duplicate outputs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if json_format:
        handler.setFormatter(StructuredJSONFormatter())
    else:
        # Readable plain text fallback for local development
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(levelname)s] (%(name)s): %(message)s "
                "[ID: %(correlation_id)s]"
            )
        )

    root_logger.addHandler(handler)


class CorrelationAndLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures:
    1. A Correlation ID is assigned to every request (read from headers or generated).
    2. Request metrics (path, method, process time, status code) are logged
       using structured formats.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Read or generate correlation ID
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        token = correlation_id_ctx.set(corr_id)

        start_time = time.perf_counter()
        logger = logging.getLogger("app.middleware")

        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time

            # Inject correlation ID back into the outbound response headers
            response.headers["X-Correlation-ID"] = corr_id

            # Structured logging on request completion
            logger.info(
                f"HTTP {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "extra_fields": {
                        "http_method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": round(process_time * 1000, 2),
                        "client_ip": request.client.host if request.client else "unknown",
                    }
                },
            )
            return response

        except Exception as exc:
            process_time = time.perf_counter() - start_time
            logger.error(
                f"HTTP Exception during processing of {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "http_method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(process_time * 1000, 2),
                    }
                },
            )
            raise exc
        finally:
            # Clean up the contextvar to prevent memory leaks across tasks
            correlation_id_ctx.reset(token)
