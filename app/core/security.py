"""
Security Utilities for IOB Platform
Phase 5: JWT tokens, password hashing, and authentication helpers.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Extract and validate user ID from JWT token."""
    if not credentials:
        raise AuthenticationError("Missing authentication credentials")
    
    payload = verify_token(credentials.credentials)
    
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    return user_id


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """Extract and validate full user payload from JWT token."""
    if not credentials:
        raise AuthenticationError("Missing authentication credentials")
    
    payload = verify_token(credentials.credentials)
    
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")
    
    return payload


def require_roles(*allowed_roles: str):
    """Dependency factory for role-based access control."""
    
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in allowed_roles):
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError(
                f"Required roles: {', '.join(allowed_roles)}",
                details={"user_roles": user_roles, "required_roles": list(allowed_roles)},
            )
        return current_user
    
    return role_checker


def require_permissions(*required_permissions: str):
    """Dependency factory for permission-based access control."""
    
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        if not all(perm in user_permissions for perm in required_permissions):
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError(
                f"Required permissions: {', '.join(required_permissions)}",
                details={
                    "user_permissions": user_permissions,
                    "required_permissions": list(required_permissions),
                },
            )
        return current_user
    
    return permission_checker