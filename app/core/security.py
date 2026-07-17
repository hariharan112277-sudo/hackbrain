"""Password, JWT, authorization, and HTTP security utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError

# Configure passlib to use hardened bcrypt defaults. Cost is controlled by the
# rounds setting while passlib retains migration support for older bcrypt hashes.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)

_http_bearer = HTTPBearer(auto_error=False)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach a conservative baseline of browser security headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password securely using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt password hash.

    Malformed or unsupported stored hashes are treated as failed credentials
    rather than being allowed to escape through an authentication endpoint.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (TypeError, ValueError):
        return False


def _jwt_secret() -> str:
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


def create_access_token(
    user_id: Union[str, Dict[str, Any], None] = None,
    role: Optional[Union[str, timedelta]] = None,
    expires_delta: Optional[timedelta] = None,
    *,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """Create an access JWT from either subject/role values or a claims mapping.

    ``data=`` remains supported for callers that use the common keyword form.
    A positional ``timedelta`` after a claims mapping is normalized to
    ``expires_delta`` so older service calls retain their intended lifetime.
    """
    if data is not None:
        if user_id is not None:
            raise TypeError("Provide either 'user_id' or 'data', not both")
        user_id = data

    if user_id is None:
        raise TypeError("A user subject or claims mapping is required")

    if isinstance(user_id, dict) and isinstance(role, timedelta):
        if expires_delta is not None:
            raise TypeError("expires_delta was provided twice")
        expires_delta = role
        role = None

    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None else timedelta(minutes=_access_expire_minutes())
    )

    if isinstance(user_id, dict):
        claims: Dict[str, Any] = dict(user_id)
        claims.update({"exp": expire, "type": "access"})
        if "role" not in claims:
            roles = claims.get("roles")
            if isinstance(roles, list) and roles:
                claims["role"] = roles[0]
        return jwt.encode(claims, _jwt_secret(), algorithm=_jwt_algorithm())

    if role is None or isinstance(role, timedelta):
        raise TypeError("A role is required when the user subject is a string")

    claims = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(claims, _jwt_secret(), algorithm=_jwt_algorithm())


def create_refresh_token(
    user_id: Union[str, Dict[str, Any], None] = None,
    expires_delta: Optional[timedelta] = None,
    *,
    role: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a refresh JWT from either subject values or a claims mapping."""
    if data is not None:
        if user_id is not None:
            raise TypeError("Provide either 'user_id' or 'data', not both")
        user_id = data
    if user_id is None:
        raise TypeError("A user subject or claims mapping is required")

    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None else timedelta(days=_refresh_expire_days())
    )

    if isinstance(user_id, dict):
        claims: Dict[str, Any] = dict(user_id)
        claims.update({"exp": expire, "type": "refresh"})
        if "role" not in claims:
            roles = claims.get("roles")
            if isinstance(roles, list) and roles:
                claims["role"] = roles[0]
        return jwt.encode(claims, _jwt_secret(), algorithm=_jwt_algorithm())

    claims = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    if role is not None:
        claims["role"] = role
    return jwt.encode(claims, _jwt_secret(), algorithm=_jwt_algorithm())


def decode_token(token: str) -> Dict[str, Any]:
    """Decode a JWT or raise a standards-compliant HTTP 401 response."""
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode an access token, returning ``None`` for invalid or expired input."""
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])
    except JWTError:
        return None
    if payload.get("type") not in (None, "access"):
        return None
    return payload


def verify_token(token: str) -> Dict[str, Any]:
    """Decode a JWT and expose domain authentication errors to service callers."""
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])
    except JWTError as exc:
        message = "Token has expired" if "expired" in str(exc).lower() else "Invalid token"
        raise AuthenticationError(message) from exc


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
) -> str:
    """Extract the subject from a valid bearer access token."""
    if not credentials:
        raise AuthenticationError("Missing authentication credentials")

    payload = verify_token(credentials.credentials)
    if payload.get("type") == "refresh":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    return str(user_id)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
) -> Dict[str, Any]:
    """Return claims from a valid bearer access token."""
    if not credentials:
        raise AuthenticationError("Missing authentication credentials")

    payload = verify_token(credentials.credentials)
    if payload.get("type") == "refresh":
        raise AuthenticationError("Invalid token type")
    return payload


def require_roles(*allowed_roles: str):
    """Build a FastAPI dependency requiring at least one allowed role."""

    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
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
    """Build a FastAPI dependency requiring every named permission."""

    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        if not all(permission in user_permissions for permission in required_permissions):
            raise AuthorizationError(
                f"Required permissions: {', '.join(required_permissions)}",
                details={
                    "user_permissions": user_permissions,
                    "required_permissions": list(required_permissions),
                },
            )
        return current_user

    return permission_checker


# Password helpers are the only wildcard-exported cryptographic interface.
# JWT and authorization functions remain explicitly importable by existing
# application wiring without widening the package's public star-import surface.
__all__ = ["hash_password", "verify_password"]
