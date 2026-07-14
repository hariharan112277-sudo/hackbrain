"""
Security & Authentication Dependency Rules.

Provides reusable FastAPI dependencies for JWT validation and role-based
access control across all Phase 4 REST controllers.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token
from app.services.user_service import UserService


security_scheme = HTTPBearer()
user_service_instance = UserService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """Decode the bearer token and return the current user's identity."""
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": payload["sub"], "roles": payload.get("roles", [])}


class RoleChecker:
    """Dependency factory that enforces one or more allowed roles."""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Depends(get_current_user)):
        user_roles = user.get("roles", [])
        if not any(role in self.allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied: Insufficient security permissions.",
            )
        return user
