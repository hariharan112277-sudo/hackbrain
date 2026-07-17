"""
AI Gateway Payload Size Guard — Phase 4 (R-4.5.1)
Industrial Operating Brain (IOB) Platform

Pure-ASGI middleware that rejects oversized request bodies targeted at the
AI Gateway proxy prefix (``/api/v1/ai``) before they are buffered, returning
an HTTP 413 envelope that matches the platform's standard error structure.

Large inference payloads can bottleneck the shared proxy event loop and
slow adjacent routing tasks; this guard enforces the strict 10MB restriction
recommended by the Phase 4 Engineering Handbook, Section 5 (AI Gateway
Integration), Recommendation R-4.5.1.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger("app.core.payload_guard")

_GUARDED_PREFIX = "/api/v1/ai"


class PayloadSizeLimitMiddleware:
    """Reject request bodies above a byte threshold on guarded prefixes.

    The check is performed in two layers:
      1. Fast-path: the declared ``Content-Length`` header (cheap rejection
         before any body bytes are read).
      2. Streaming guard: cumulative byte counting on ``http.request``
         messages so chunked uploads cannot bypass the limit.
    """

    def __init__(
        self,
        app: Callable,
        max_bytes: Optional[int] = None,
        prefix: str = _GUARDED_PREFIX,
    ) -> None:
        self.app = app
        self.max_bytes = max_bytes if max_bytes is not None else settings.AI_GATEWAY_MAX_PAYLOAD_BYTES
        self.prefix = prefix

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> Any:
        if scope.get("type") != "http" or not scope.get("path", "").startswith(self.prefix):
            return await self.app(scope, receive, send)

        # Layer 1 — declared Content-Length header
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        declared = headers.get("content-length")
        if declared is not None:
            try:
                if int(declared) > self.max_bytes:
                    logger.warning(
                        "ai_gateway_payload_rejected",
                        path=scope.get("path"),
                        declared_bytes=int(declared),
                        limit_bytes=self.max_bytes,
                    )
                    return await self._send_413(send)
            except ValueError:
                pass  # malformed header — let downstream validation handle it

        # Layer 2 — streamed body byte counter (guards chunked transfer)
        received_bytes = 0
        rejected = False

        async def guarded_receive() -> dict:
            nonlocal received_bytes, rejected
            message = await receive()
            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_bytes:
                    rejected = True
                    # Truncate: stop feeding body to the application
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        try:
            await self.app(scope, guarded_receive, send)
        finally:
            if rejected:
                logger.warning(
                    "ai_gateway_streamed_payload_truncated",
                    path=scope.get("path"),
                    received_bytes=received_bytes,
                    limit_bytes=self.max_bytes,
                )

    async def _send_413(self, send: Callable) -> None:
        body = json.dumps(
            {
                "success": False,
                "error": "PAYLOAD_TOO_LARGE",
                "message": (
                    "AI Gateway request payload exceeds the "
                    f"{self.max_bytes // (1024 * 1024)}MB limit (R-4.5.1)."
                ),
                "details": {"limit_bytes": self.max_bytes},
            }
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("latin-1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


__all__ = ["PayloadSizeLimitMiddleware"]
