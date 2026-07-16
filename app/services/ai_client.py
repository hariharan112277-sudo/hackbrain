"""HTTP client used by the transparent AI gateway routes."""

from __future__ import annotations

from typing import Any, Literal, Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

_HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


async def call_ai(
    path: str,
    *,
    payload: Optional[dict[str, Any]] = None,
    method: _HTTPMethod = "POST",
) -> dict[str, Any]:
    """Call the configured AI service and return its JSON object response.

    Transport failures are converted to gateway errors. Upstream HTTP status
    codes are retained so API consumers can distinguish validation failures
    from unavailable infrastructure.
    """
    if not path.startswith("/"):
        raise ValueError("AI service paths must start with '/'")

    url = f"{settings.AI_SERVICE_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT) as client:
            response = await client.request(method, url, json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service request timed out",
        ) from exc
    except httpx.HTTPStatusError as exc:
        detail: Any
        try:
            detail = exc.response.json()
        except ValueError:
            detail = exc.response.text or "AI service rejected the request"
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service is unavailable",
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned a non-JSON response",
        ) from exc
    if not isinstance(result, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned an invalid response object",
        )
    return result


__all__ = ["call_ai"]
