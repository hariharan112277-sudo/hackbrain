"""
Custom Exception Hierarchy for IOB Platform
Phase 5: Structured error handling with error codes and details.

Phase 1 (Stability Hardening):
    Serialization-safe global exception handlers were appended below so that
    malformed/binary payloads (which surface un-decoded ``bytes`` inside
    ``RequestValidationError.errors()``) can never escalate a client 4xx into a
    500 Internal Server Error. See ``request_validation_exception_handler`` and
    the SQLAlchemy / global handlers.
"""

from typing import Any, Dict, Optional

# --- Phase 1: Stability Hardening (serialization-safe exception handlers) ---
import logging

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DBAPIError
import datetime
import decimal
import enum
import uuid


class IOBException(Exception):
    """Base exception for all IOB application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ResourceNotFoundError(IOBException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details={**details, "resource_type": resource_type, "resource_id": resource_id},
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(IOBException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details or {},
        )


class AuthenticationError(IOBException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
            details=details or {},
        )


class AuthorizationError(IOBException):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
            details=details or {},
        )


class RateLimitError(IOBException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={**details, "retry_after": retry_after},
        )


class ExternalServiceError(IOBException):
    """Raised when an external service call fails."""

    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"External service '{service}' error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={**details, "service": service},
        )


class ConfigurationError(IOBException):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details or {},
        )


class RepositoryError(IOBException):
    """Raised when repository operations fail."""

    def __init__(
        self,
        operation: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Repository operation '{operation}' failed: {message}",
            error_code="REPOSITORY_ERROR",
            status_code=500,
            details={**details, "operation": operation},
        )


# =============================================================================
# PHASE 1 — Critical Backend Bug Fixes & Stability Hardening
# Serialization-safe global exception handlers.
#
# Root cause (Task 1): the previous inline RequestValidationError handler passed
# ``exc.errors()`` straight into ``JSONResponse``. When the error dict contains
# un-decoded ``bytes`` (raw body fragments, corrupted UTF-8, binary injection),
# ``json.dumps`` raised ``TypeError: Object of type bytes is not JSON
# serializable`` and escalated the client's 422 into a 500. ``jsonable_encoder``
# recursively sanitizes nested structures (bytes -> safe string, datetimes,
# decimals, Enums, UUIDs, custom objects) before serialization.
# =============================================================================

logger = logging.getLogger("iob.backend.recovery")


def sanitize_payload(obj: Any) -> Any:
    """Recursively convert arbitrary data into strict JSON-safe primitives.

    ``fastapi.encoders.jsonable_encoder`` only decodes *valid UTF-8* bytes and
    raises ``UnicodeDecodeError`` on binary payloads (e.g. VAL-002 raw
    ``\\x00\\xFF\\xAA``). This helper closes that gap: raw bytes (including
    invalid UTF-8) are decoded with ``errors="backslashreplace"`` so they can
    never crash serialization, while UUIDs / datetimes / Decimals / Enums / sets
    are normalized explicitly.
    """
    # Raw bytes / bytearray — the core Task 1 bug vector.
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj).decode("utf-8", errors="backslashreplace")
    # JSON-native scalars.
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, dict):
        return {str(k): sanitize_payload(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [sanitize_payload(v) for v in obj]
    # Fallback for Pydantic models / dataclasses / unknown objects.
    try:
        return jsonable_encoder(obj)
    except (TypeError, UnicodeDecodeError, ValueError):
        return str(obj)


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Any] = None,
) -> "JSONResponse":
    """Enforce the strict Phase 1 error schema contract across all exceptions."""
    from fastapi.responses import JSONResponse

    payload = {
        "success": False,
        "error": error_code,
        "message": message,
        "details": sanitize_payload(details) if details else [],
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> "JSONResponse":
    """422 — malformed / garbage payloads.

    Uses ``jsonable_encoder`` so bytes/non-JSON fragments inside the error dict
    can never crash serialization.
    """
    logger.warning(
        "Request validation failure on path %s: %s",
        str(request.url.path),
        str(exc),
    )
    safe_details = sanitize_payload(exc.errors())
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="The request payload or parameter format is invalid.",
        details=safe_details,
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> "JSONResponse":
    """422 — internal model / response serialization validation crash."""
    logger.error(
        "Internal validation crash on path %s: %s",
        str(request.url.path),
        str(exc),
    )
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="INTERNAL_VALIDATION_ERROR",
        message="Data validation failed within the application processing boundary.",
        details=sanitize_payload(exc.errors()),
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> "JSONResponse":
    """Map DB-layer failures uniformly — never leak raw traces to the client."""
    logger.critical(
        "Database infrastructure exception on path %s: %s",
        str(request.url.path),
        str(exc),
    )
    if isinstance(exc, IntegrityError):
        return create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            error_code="DATABASE_INTEGRITY_VIOLATION",
            message="Operation violates database uniqueness or relationship constraints.",
        )
    # Covers DBAPIError, ConnectionError and TimeoutError surfaced from the engine.
    return create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_code="DATABASE_UNAVAILABLE",
        message="Persistent storage engine is temporarily unable to fulfill the request.",
    )


async def general_exception_handler(request: Request, exc: Exception) -> "JSONResponse":
    """Absolute safety fallback — strict JSON contract for any unhandled error."""
    logger.error(
        "Unhandled system exception on path %s: %s",
        str(request.url.path),
        str(exc),
        exc_info=True,
    )
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected system error occurred. Engineers have been notified.",
    )


__all__ = [
    "IOBException",
    "ResourceNotFoundError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ExternalServiceError",
    "ConfigurationError",
    "RepositoryError",
    "create_error_response",
    "request_validation_exception_handler",
    "pydantic_validation_exception_handler",
    "sqlalchemy_exception_handler",
    "general_exception_handler",
]
