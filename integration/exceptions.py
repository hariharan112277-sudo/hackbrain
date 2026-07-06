"""
IOB Integration Domain Exceptions.
Standardizes structural exception tracking for consuming backend domains.
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


class MQTTTransportException(IOBIntegrationException):
    """Raised when the underlying broker fabric is disconnected or unreachable."""


class DatabaseUnavailableException(IOBIntegrationException):
    """Raised when persistence lookups timeout or connections drop."""


class InvalidQueryCriteriaException(IOBIntegrationException):
    """Raised when range filters, pagination bounds, or sort elements violate validation."""


class ConfigurationValidationException(IOBIntegrationException):
    """Raised when critical configuration profiles are malformed or missing."""
