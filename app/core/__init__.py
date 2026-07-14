"""
Core configuration and utilities for IOB Platform.
"""

from app.core.config import settings
from app.core.exceptions import (
    IOBException,
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ExternalServiceError,
)
from app.core.security import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password,
)

__all__ = [
    "settings",
    "IOBException",
    "ResourceNotFoundError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ExternalServiceError",
    "create_access_token",
    "verify_token",
    "get_password_hash",
    "verify_password",
]