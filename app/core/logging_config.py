"""Structured JSON logging and request correlation for production."""
from __future__ import annotations

import contextvars
import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

import structlog

from app.core.config import settings

correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")


class StructuredJSONFormatter(logging.Formatter):
    """Emit a stable, JSON-serialisable log contract."""
    _reserved = set(logging.LogRecord(None, 0, "", 0, "", (), None).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        value: Any = record.getMessage()
        event: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "message": value,
            "correlation_id": correlation_id_ctx.get(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            event.update(extra)
        if record.exc_info:
            event["exception"] = "".join(traceback.format_exception(*record.exc_info)).strip()
        return json.dumps(event, default=str, ensure_ascii=False)


def setup_structured_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Idempotently configure stdlib logging (useful for tests and workers)."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJSONFormatter() if json_format else logging.Formatter("%(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)


def setup_logging() -> None:
    """Configure structlog on top of the JSON stdlib handler."""
    setup_structured_logging(settings.LOG_LEVEL, settings.JSON_LOGS)
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )


def get_logger(name: str):
    return structlog.get_logger(name)


class CorrelationAndLoggingMiddleware:
    """ASGI middleware that propagates a bounded request correlation ID."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-correlation-id", b"").decode("latin-1")[:128]
        if not request_id:
            import uuid
            request_id = str(uuid.uuid4())
        token = correlation_id_ctx.set(request_id)
        status_code = 500
        started = False
        async def send_wrapper(message):
            nonlocal status_code, started
            if message["type"] == "http.response.start":
                started = True
                status_code = message["status"]
                message["headers"] = list(message.get("headers", [])) + [(b"x-correlation-id", request_id.encode())]
            await send(message)
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            if not started:
                body = b"Internal Server Error"
                await send({"type": "http.response.start", "status": 500, "headers": [(b"content-type", b"text/plain"), (b"content-length", str(len(body)).encode()), (b"x-correlation-id", request_id.encode())]})
                await send({"type": "http.response.body", "body": body})
        finally:
            correlation_id_ctx.reset(token)


# Backwards-compatible name used by the earlier integration module.
LoggingMiddleware = CorrelationAndLoggingMiddleware
