"""
AI Client Service
Phase 5 & Phase 1 Remediation: Relay client for communicating with the external AI service platform.
"""

from typing import Any, Optional
import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger("app.services.ai_client")


async def call_ai(
    endpoint: str,
    payload: Optional[dict[str, Any]] = None,
    method: str = "GET",
) -> dict[str, Any]:
    """
    Transparently relays an API call to the external enterprise AI service.

    Parameters:
        endpoint: Destination path relative to settings.AI_SERVICE_URL (e.g. '/api/v1/chat').
        payload:  Optional JSON dictionary payload for POST/PUT.
        method:   HTTP method string (GET, POST, etc.).

    Returns:
        JSON response parsed from the external service.
    """
    # Build complete destination URL
    base_url = settings.AI_SERVICE_URL.rstrip("/")
    target_path = "/" + endpoint.lstrip("/")
    url = f"{base_url}{target_path}"

    logger.info("Relaying request to external AI service", url=url, method=method)

    try:
        timeout_val = getattr(settings, "AI_SERVICE_TIMEOUT", 5.0)
        async with httpx.AsyncClient(timeout=timeout_val) as client:
            if method.upper() == "POST":
                response = await client.post(url, json=payload)
            elif method.upper() == "PUT":
                response = await client.put(url, json=payload)
            elif method.upper() == "DELETE":
                response = await client.delete(url)
            else:
                response = await client.get(url)

            response.raise_for_status()
            # Try parsing response JSON
            return response.json()

    except httpx.HTTPStatusError as exc:
        logger.error(
            "AI service returned HTTP error status",
            status_code=exc.response.status_code,
            url=url,
            response_text=exc.response.text,
        )
        return {
            "success": False,
            "error": "AI_SERVICE_HTTP_ERROR",
            "status_code": exc.response.status_code,
            "message": f"AI service returned error: {exc.response.text}",
        }
    except httpx.RequestError as exc:
        logger.error("AI service connectivity issue", url=url, error=str(exc))
        return {
            "error": {
                "code": "AI_UNAVAILABLE",
                "message": "AI service is temporarily unavailable",
            }
        }
    except Exception as exc:
        logger.error("Unexpected error in AI client service", url=url, error=str(exc))
        return {
            "success": False,
            "error": "INTERNAL_CLIENT_ERROR",
            "message": str(exc),
        }
