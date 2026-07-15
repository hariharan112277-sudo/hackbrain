"""
Standardised error helpers — Track A (Hariharan) — Stage 2 (Authentication)

Provides ``error_envelope`` so authentication endpoints return a consistent
structured error body without scattering ad-hoc HTTPException construction.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


def error_envelope(
    code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    *,
    details: Optional[Dict[str, Any]] = None,
) -> HTTPException:
    """
    Build (and is intended to be raised as) a structured HTTPException.

    Usage::

        raise error_envelope("INVALID_CREDENTIALS", "Email or password is incorrect", 401)

    Response body shape::

        {
          "error_code": "<code>",
          "message": "<message>",
          "details": { ... }          # only present when provided
        }
    """
    body: Dict[str, Any] = {
        "error_code": code,
        "message": message,
    }
    if details:
        body["details"] = details

    headers = None
    if status_code == status.HTTP_401_UNAUTHORIZED:
        headers = {"WWW-Authenticate": "Bearer"}

    return HTTPException(
        status_code=status_code,
        detail=body,
        headers=headers,
    )


__all__ = ["error_envelope"]
