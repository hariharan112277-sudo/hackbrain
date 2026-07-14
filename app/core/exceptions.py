"""
Custom Global Exception Handling Module.

Defines clean domain/application-level errors and global handlers to convert
them into uniform, sanitized JSON schemas. This module provides:

Domain Exceptions:
- AppBaseException: Base class for all domain-specific application exceptions
- AuthenticationError: Raised when authentication fails (401)
- ResourceNotFoundError: Raised when a requested resource is missing (404)

Exception Handlers:
- custom_app_exception_handler: Handles AppBaseException subclasses
- iob_integration_exception_handler: Handles IOB integration domain exceptions
- pydantic_validation_exception_handler: Sanitizes Pydantic parsing errors
- global_starlette_exception_handler: Catches Starlette HTTPExceptions
- default_unhandled_exception_handler: Ultimate safety net for 500 errors

All error responses follow a consistent JSON schema:
{
    "success": false,
    "error": "<ExceptionClassName>",
    "message": "<human-readable message>",
    "details": <structured details or null>
}
"""
from typing import Any, Dict
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# =============================================================================
# Domain Exception Classes
# =============================================================================

class AppBaseException(Exception):
    """Base class for all domain-specific application exceptions."""

    def __init__(self, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(AppBaseException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Invalid credentials or missing token",
        details: Any = None,
    ):
        super().__init__(message=message, status_code=401, details=details)


class ResourceNotFoundError(AppBaseException):
    """Raised when a requested resource is missing."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"Resource '{resource}' matching identifier '{identifier}' was not found.",
            status_code=404,
        )


# =============================================================================
# Global Exception Handlers
# =============================================================================

async def custom_app_exception_handler(
    request: Request, exc: AppBaseException
) -> JSONResponse:
    """Handles custom domain-level exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Sanitizes Pydantic parsing errors into a clean, uniform list."""
    errors = []
    for error in exc.errors():
        # Clean up locations (e.g. ['body', 'username'] -> 'username')
        loc = " -> ".join([str(x) for x in error["loc"]])
        errors.append(
            {
                "field": loc,
                "issue": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "ValidationError",
            "message": "Input payload schema validation failed.",
            "details": errors,
        },
    )


async def global_starlette_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Catches direct HTTPExceptions raised by FastAPI or Starlette internals."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTPException",
            "message": exc.detail,
            "details": None,
        },
    )


async def default_unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Ultimate safety net catching raw unhandled system faults.
    Prevents stack trace leakage to clients in production.
    """
    # Note: Logged automatically by our CorrelationAndLoggingMiddleware
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "InternalServerError",
            "message": "An unexpected server error occurred. Please contact system support.",
            "details": None,
        },
    )


# =============================================================================
# IOB Integration Exception Handler (bridges integration.exceptions)
# =============================================================================

async def iob_integration_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handles IOB integration domain exceptions from integration.exceptions.
    Maps integration-layer exceptions to appropriate HTTP status codes
    while maintaining the uniform JSON error schema.
    """
    # Map integration exceptions to status codes
    status_map = {
        "ResourceNotFoundError": 404,
        "InvalidQueryCriteriaException": 422,
        "ConfigurationValidationException": 500,
        "MQTTTransportException": 503,
        "DatabaseUnavailableException": 503,
    }

    exc_type = exc.__class__.__name__
    status_code = status_map.get(exc_type, 500)

    # Extract message and details if available
    message = getattr(exc, "message", str(exc))
    details = getattr(exc, "details", None)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": exc_type,
            "message": message,
            "details": details,
        },
    )


# =============================================================================
# Registration Helper
# =============================================================================

def register_exception_handlers(app) -> None:
    """
    Register all exception handlers on the FastAPI application.

    This is a convenience function that registers all handlers at once.
    Call this during application factory setup.

    Args:
        app: The FastAPI application instance.
    """
    # Import IOB integration exception base class
    from integration.exceptions import IOBIntegrationException

    app.add_exception_handler(AppBaseException, custom_app_exception_handler)
    app.add_exception_handler(
        IOBIntegrationException, iob_integration_exception_handler
    )
    app.add_exception_handler(
        RequestValidationError, pydantic_validation_exception_handler
    )
    app.add_exception_handler(
        StarletteHTTPException, global_starlette_exception_handler
    )
    app.add_exception_handler(Exception, default_unhandled_exception_handler)
