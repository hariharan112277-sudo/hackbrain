"""
Custom Exception Hierarchy for IOB Platform
Phase 5: Structured error handling with error codes and details.
"""

from typing import Any, Dict, Optional


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