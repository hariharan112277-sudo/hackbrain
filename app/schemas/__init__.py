"""
Pydantic schema package for Phase 4 REST APIs.

Provides strongly-typed request / response models for:
- Authentication (auth)
- User management (users)
- Industrial data (machines, telemetry, alarms, metadata)
- Dashboard aggregation

All response envelopes follow the standard `{success, data, error, meta}` shape.
"""
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """Uniform API response envelope used across all Phase 4 endpoints."""

    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class PaginationMeta(BaseModel):
    """Pagination metadata attached to list responses."""

    page: int = 1
    page_size: int = 100
    total: Optional[int] = None
    next_cursor: Optional[str] = None


__all__ = [
    "StandardResponse",
    "PaginationMeta",
]
