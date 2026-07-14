"""
IOB Integration Domain Exceptions.

Standardizes structural exception tracking for consuming backend domains.

This module defines domain-specific exceptions for the integration layer.
These exceptions are designed to be caught by the global exception handlers
registered in app.core.exceptions, which convert them into uniform JSON responses.

The integration exceptions inherit from IOBIntegrationException (base class)
and are separate from the application-level AppBaseException hierarchy.
Both are handled by the global exception handler pipeline.
"""
from typing import Optional, Dict, Any


class IOBIntegrationException(Exception):
    """Base exception for all integration and service tier boundary errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ResourceNotFoundError(IOBIntegrationException):
    """Raised when an asset, machine, sensor, or entity lookup fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class MQTTTransportException(IOBIntegrationException):
    """Raised when the underlying broker fabric is disconnected or unreachable."""


class DatabaseUnavailableException(IOBIntegrationException):
    """Raised when persistence lookups timeout or connections drop."""


class InvalidQueryCriteriaException(IOBIntegrationException):
    """Raised when range filters, pagination bounds, or sort elements violate validation."""


class ConfigurationValidationException(IOBIntegrationException):
    """Raised when critical configuration profiles are malformed or missing."""
