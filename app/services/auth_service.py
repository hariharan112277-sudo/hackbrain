"""
Authentication Service
Phase 5: User authentication, token management, and session handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
)
from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    ResourceNotFoundError,
)
from app.schemas.auth import LoginRequest, RegisterRequest, Token, TokenData
from app.repositories.interfaces import IUserRepository

logger = structlog.get_logger("app.services.auth")


class AuthService:
    """Authentication and authorization business logic."""

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, login_data: LoginRequest) -> Token:
        """Authenticate user credentials and return tokens."""
        user = await self.user_repo.get_by_email(login_data.email)
        
        if not user:
            logger.warning("auth_login_failed_user_not_found", email=login_data.email)
            raise AuthenticationError("Invalid credentials")
        
        if not user.get("is_active", True):
            logger.warning("auth_login_failed_inactive", email=login_data.email)
            raise AuthenticationError("Account is disabled")
        
        if not verify_password(login_data.password, user["password_hash"]):
            logger.warning("auth_login_failed_invalid_password", email=login_data.email)
            raise AuthenticationError("Invalid credentials")
        
        # Update last login
        await self.user_repo.update_last_login(user["id"])
        
        # Create tokens
        token_data = {
            "sub": str(user["id"]),
            "email": user["email"],
            "roles": user.get("roles", []),
            "permissions": user.get("permissions", []),
        }
        
        expires_delta = None
        if login_data.remember_me:
            expires_delta = timedelta(days=7)
        
        access_token = create_access_token(token_data, expires_delta)
        refresh_token = create_refresh_token(token_data)
        
        logger.info("auth_login_success", user_id=str(user["id"]), email=user["email"])
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800 if not login_data.remember_me else 604800,
        )

    async def register_user(self, register_data: RegisterRequest) -> Token:
        """Register a new user and return tokens."""
        # Check if email exists
        existing = await self.user_repo.get_by_email(register_data.email)
        if existing:
            raise ValidationError("Email already registered", details={"email": register_data.email})
        
        # Hash password
        password_hash = get_password_hash(register_data.password)
        
        # Create user
        user_data = {
            "id": uuid4(),
            "email": register_data.email,
            "full_name": register_data.full_name,
            "password_hash": password_hash,
            "is_active": True,
            "roles": [register_data.role] if register_data.role else ["operator"],
            "permissions": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        user = await self.user_repo.create(user_data)
        
        # Create tokens
        token_data = {
            "sub": str(user["id"]),
            "email": user["email"],
            "roles": user.get("roles", []),
            "permissions": user.get("permissions", []),
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info("auth_register_success", user_id=str(user["id"]), email=user["email"])
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800,
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        from app.core.security import verify_token
        
        try:
            payload = verify_token(refresh_token)
        except AuthenticationError:
            raise AuthenticationError("Invalid refresh token")
        
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        # Verify user still exists and is active
        user = await self.user_repo.get_by_id(UUID(payload["sub"]))
        if not user or not user.get("is_active", True):
            raise AuthenticationError("User not found or inactive")
        
        # Create new tokens
        token_data = {
            "sub": str(user["id"]),
            "email": user["email"],
            "roles": user.get("roles", []),
            "permissions": user.get("permissions", []),
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=1800,
        )

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        if not verify_password(current_password, user["password_hash"]):
            raise AuthenticationError("Current password is incorrect")
        
        new_hash = get_password_hash(new_password)
        await self.user_repo.update_password(user_id, new_hash)
        
        logger.info("auth_password_changed", user_id=str(user_id))
        return True

    async def validate_token(self, token: str) -> TokenData:
        """Validate and decode access token."""
        from app.core.security import verify_token
        
        payload = verify_token(token)
        
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        
        return TokenData(**payload)