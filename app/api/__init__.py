"""
Phase 4 REST API router package.
"""
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.industrial import router as industrial_router
from app.api.dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "users_router",
    "industrial_router",
    "dashboard_router",
]
