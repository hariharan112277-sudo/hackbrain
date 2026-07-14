"""
Security Headers & JWT Foundation Module.

Provides enterprise-grade security utilities:
- SecurityHeadersMiddleware: Injects strict security headers (XSS, clickjacking, etc.)
- Password hashing: Argon2/Bcrypt via passlib
- JWT encoding/decoding: Secure token generation with expiration

Security Headers Injected:
- X-Frame-Options: DENY (clickjacking protection)
- X-Content-Type-Options: nosniff (MIME sniffing protection)
- X-XSS-Protection: 1; mode=block (XSS filter)
- Content-Security-Policy: default-src 'self'; frame-ancestors 'none'
- Strict-Transport-Security: max-age=31536000; includeSubDomains (HSTS)
- Referrer-Policy: strict-origin-when-cross-origin
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

# Password hashing configuration (using Argon2 by default for enterprise security)
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects robust security headers protecting against common web vulnerabilities."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none';"
        )
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def hash_password(password: str) -> str:
    """Hashes a plain-text password securely."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed match."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Generates a secure, cryptographically signed JWT."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT signature and expiration."""
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        return (
            decoded_token
            if decoded_token["exp"] >= datetime.now(timezone.utc).timestamp()
            else None
        )
    except JWTError:
        return None
