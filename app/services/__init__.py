"""
Business service composition root.
"""
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.industrial_service import IndustrialService
from app.services.dashboard_service import DashboardService

__all__ = [
    "AuthService",
    "UserService",
    "IndustrialService",
    "DashboardService",
]
