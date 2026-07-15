"""
Security Utilities — Track A (Hariharan) — Stage 2 (Authentication)
Industrial Operating Brain (IOB) Platform

Implements:
  * bcrypt password hashing / verification
  * HS256 JWT access + refresh token lifecycle
  * Safe token decoding with HTTP 401 on failure

Backward-compatible surface for Phase 5 / Stage 0 callers:
  * get_password_hash  → alias of hash_password
  * verify_token       → AuthenticationError bridge used by app.deps
  * create_access_token / create_refresh_token accept Stage-2 *or* Phase-5 signatures
  * get_current_user / get_current_user_id / require_roles / require_permissions
    remain available for existing Phase-5 routers (users / industrial / dashboard)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError

# ---------------------------------------------------------------------------
# Password hashing (bcrypt)
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Optional bearer scheme used by the Phase-5 helpers below.
_http_bearer = HTTPBearer(auto_error=False)


def _jwt_secret() -> str:
    """Resolve JWT signing secret (Stage-2 name → Phase-5 name)."""
    return getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY


def _jwt_algorithm() -> str:
    return getattr(settings, "ALGORITHM", "HS256") or "HS256"


def _access_expire_minutes() -> int:
    return int(
        getattr(settings, "JWT_EXPIRE_MINUTES", None)
        or getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    )


def _refresh_expire_days() -> int:
    return int(getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7))


# =====================================================================
# Stage 2 — Password utilities
# =====================================================================

def hash_password(plain_password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed bcrypt password."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# Phase-5 alias (auth_service / user_service import this name)
def get_password_hash(password: str) -> str:
    """Alias of ``hash_password`` kept for Phase-5 callers."""
    return hash_password(password)


# =====================================================================
# Stage 2 — JWT token lifecycle
# =====================================================================

def create_access_token(
    user_id: Union[str, Dict[str, Any]],
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generate an HS256 JWT access token.

    Stage-2 signature
        create_access_token(user_id: str, role: str) -> str
        Payload: ``sub``, ``role``, ``exp``  (+ ``type=access`` for Stage-0)

    Phase-5 signature (preserved)
        create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str
        ``data`` is merged into the payload; ``type=access`` is forced.
    """
    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=_access_expire_minutes())

    if isinstance(user_id, dict):
        # Phase-5 path: first arg is a claims dictionary
        to_encode: Dict[str, Any] = dict(user_id)
        to_encode.update({"exp": expire, "type": "access"})
        # Normalise primary role claim so Stage-0 UserContext can resolve it
        if "role" not in to_encode:
            roles = to_encode.get("roles")
            if isinstance(roles, list) and roles:
                to_encode["role"] = roles[0]
        return jwt.encode(to_encode, _jwt_secret(), algorithm=_jwt_algorithm())

    # Stage-2 path: (user_id, role)
    if role is None:
        raise TypeError(
            "create_access_token(user_id, role) requires 'role' when user_id is a string"
        )
    to_encode = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(to_encode, _jwt_secret(), algorithm=_jwt_algorithm())


def create_refresh_token(
    user_id: Union[str, Dict[str, Any]],
    expires_delta: Optional[timedelta] = None,
    *,
    role: Optional[str] = None,
) -> str:
    """
    Generate an HS256 JWT refresh token.

    Stage-2 signature
        create_refresh_token(user_id: str) -> str
        Valid for 7 days. Payload: ``sub``, ``type=refresh``, ``exp``.
        Optionally embeds ``role`` so /refresh can re-issue a correct access token.

    Phase-5 signature (preserved)
        create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str
    """
    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=_refresh_expire_days())

    if isinstance(user_id, dict):
        to_encode: Dict[str, Any] = dict(user_id)
        to_encode.update({"exp": expire, "type": "refresh"})
        if "role" not in to_encode:
            roles = to_encode.get("roles")
            if isinstance(roles, list) and roles:
                to_encode["role"] = roles[0]
        return jwt.encode(to_encode, _jwt_secret(), algorithm=_jwt_algorithm())

    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    if role is not None:
        to_encode["role"] = role
    return jwt.encode(to_encode, _jwt_secret(), algorithm=_jwt_algorithm())


def decode_token(token: str) -> Dict[str, Any]:
    """
    Safely decode an HS256 token.

    Raises HTTP 401 Unauthorized if the token signature is invalid,
    expired, or structurally corrupted.
    """
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[_jwt_algorithm()],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =====================================================================
# Phase-5 / Stage-0 bridge — verify_token (raises AuthenticationError)
# =====================================================================

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.

    Used by ``app.deps.decode_token`` which converts ``AuthenticationError``
    into a standard FastAPI ``HTTPException(401)``.
    """
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[_jwt_algorithm()],
        )
        return payload
    except JWTError as exc:
        # Distinguish expiry where possible for clearer messages
        msg = str(exc).lower()
        if "expired" in msg:
            raise AuthenticationError("Token has expired")
        raise AuthenticationError("Invalid token")


# =====================================================================
# Phase-5 helpers — used by users / industrial / dashboard routers
# =====================================================================

async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
) -> str:
    """Extract and validate user ID from JWT token (Phase-5 helper)."""
    if not credentials:
        raise AuthenticationError("Missing authentication credentials")

    payload = verify_token(credentials.credentials)

    if payload.get("type") not in (None, "access"):
        # Allow tokens without explicit type (Stage-2 pure form) or type=access
        if payload.get("type") == "refresh":
            raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    return user_id


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
) -> Dict[str, Any]:
    """Extract and validate full user payload from JWT token (Phase-5 helper)."""
    if not credentials:
        raise AuthenticationError("Missing authentication credentials")

    payload = verify_token(credentials.credentials)

    if payload.get("type") == "refresh":
        raise AuthenticationError("Invalid token type")

    return payload


def require_roles(*allowed_roles: str):
    """Dependency factory for role-based access control (Phase-5)."""

    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        # Support both single ``role`` claim (Stage-2) and ``roles`` list (Phase-5)
        user_roles = current_user.get("roles") or []
        if not user_roles and current_user.get("role"):
            user_roles = [current_user["role"]]
        if not any(role in user_roles for role in allowed_roles):
            raise AuthorizationError(
                f"Required roles: {', '.join(allowed_roles)}",
                details={"user_roles": user_roles, "required_roles": list(allowed_roles)},
            )
        return current_user

    return role_checker


def require_permissions(*required_permissions: str):
    """Dependency factory for permission-based access control (Phase-5)."""

    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        if not all(perm in user_permissions for perm in required_permissions):
            raise AuthorizationError(
                f"Required permissions: {', '.join(required_permissions)}",
                details={
                    "user_permissions": user_permissions,
                    "required_permissions": list(required_permissions),
                },
            )
        return current_user

    return permission_checker


__all__ = [
    "pwd_context",
    "hash_password",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    "get_current_user",
    "get_current_user_id",
    "require_roles",
    "require_permissions",
]
