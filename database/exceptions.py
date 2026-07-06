"""
Custom domain exceptions for the Industrial Operating Brain Database Layer.
Provides targeted diagnostic tracing without leakage of low-level driver implementations.
"""


class IOBDatabaseError(Exception):
    """Base exception for all domain-specific errors in the IOB storage subsystem."""
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception


class ConnectionError(IOBDatabaseError):
    """Raised when the infrastructure cannot reach the target PostgreSQL cluster."""


class OperationalTimeoutError(IOBDatabaseError):
    """Raised when transactional or query logic violates predefined operational execution limits."""


class ConstraintViolationError(IOBDatabaseError):
    """Raised when a unique, foreign key, or check constraint check fails."""


class RecordNotFoundError(IOBDatabaseError):
    """Raised when an explicit lookup identity fails to return structural entity matches."""


class BulkOperationError(IOBDatabaseError):
    """Raised when a transactional bulk data array processing batch fails execution criteria."""
