"""
FastAPI Dependencies — Track A (Hariharan) — Stage 0 (Dependency Layer)
Industrial Operating Brain (IOB) Platform

Canonical import point for:
  1. Database session dependency (re-exported from app.database)
  2. JWT authentication security context  →  UserContext
  3. Role-Based Access Control (RBAC) dependency factory

Usage (database):
    from app.deps import DBSession
    @router.get("/assets")
    def list_assets(db: DBSession):
        ...

Usage (authentication):
    from app.deps import get_current_user, UserContext
    @router.get("/profile")
    def profile(user: UserContext = Depends(get_current_user)):
        ...

Usage (RBAC):
    from app.deps import require_role, UserContext
    @router.delete("/machines/{id}")
    def delete_machine(id: str, user: UserContext = Depends(require_role("admin", "supervisor"))):
        ...

Downstream dependency:
    Track B (Lathika) — app/api/ws.py WebSocket authentication
    must NOT be built until this file is merged.

Note:
    app.core.dependencies (service/repository providers) is intentionally
    NOT re-exported here — import it directly where needed.
"""

from __future__ import annotations

from typing import Annotated, Any, Callable, Dict, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# ── Internal imports (existing wiring) ──────────────────────────────────
from app.database import get_db
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError

# =====================================================================
# 1. DATABASE SESSION DEPENDENCY  (preserved from Track A Stage 1)
# =====================================================================

# Convenient annotated alias: `db: DBSession` in route signatures.
DBSession = Annotated[Session, Depends(get_db)]


# =====================================================================
# 2. OAUTH2 TOKEN SCHEME
# =====================================================================

# Points the Swagger UI "Authorize" dialog at the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# =====================================================================
# 3. USER CONTEXT  (structured identity container)
# =====================================================================

class UserContext:
    """
    Structured context container holding the validated user's identity
    and primary system role, extracted from the JWT payload.

    Attributes:
        user_id: The subject claim ('sub') from the JWT — unique user identifier.
        role:    The primary role claim from the JWT (e.g. 'admin', 'operator',
                 'viewer', 'supervisor').
    """

    __slots__ = ("user_id", "role")

    def __init__(self, user_id: str, role: str) -> None:
        self.user_id = user_id
        self.role = role

    # ── Dunder helpers for logging / debugging ──────────────────────
    def __repr__(self) -> str:  # pragma: no cover
        return f"UserContext(user_id={self.user_id!r}, role={self.role!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserContext):
            return NotImplemented
        return self.user_id == other.user_id and self.role == other.role

    def __hash__(self) -> int:
        return hash((self.user_id, self.role))


# =====================================================================
# 4. TOKEN DECODING  (bridge to app.core.security.verify_token)
# =====================================================================

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Thin wrapper around ``app.core.security.verify_token`` that converts
    the project-level ``AuthenticationError`` into a standard FastAPI
    ``HTTPException(401)`` so that endpoint code can rely on a single
    exception type for authentication failures.

    Parameters:
        token: Raw JWT string (without the 'Bearer ' prefix).

    Returns:
        Decoded payload dictionary.

    Raises:
        HTTPException(401): If the token is expired, malformed, or
                            has an invalid signature.
    """
    try:
        payload: Dict[str, Any] = verify_token(token)
        return payload
    except AuthenticationError as exc:
        # verify_token raises AuthenticationError for expired / invalid tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


# =====================================================================
# 5. CURRENT-USER DEPENDENCY
# =====================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> UserContext:
    """
    FastAPI dependency that decodes the inbound JWT bearer token and
    returns a validated ``UserContext``.

    The token is extracted automatically by ``OAuth2PasswordBearer``
    from the ``Authorization: Bearer <token>`` header.

    Raises:
        HTTPException(401): If the token is invalid, expired, or
                            missing the ``sub`` / ``role`` claims.
    """
    payload = decode_token(token)

    # ── Claim validation ────────────────────────────────────────────
    # The spec mandates both 'sub' and 'role' be present.
    # We also accept 'roles' (list) for backward-compatibility with
    # tokens issued by the existing auth service (see core/security.py).
    user_id: str | None = payload.get("sub")

    role: str | None = payload.get("role")
    if role is None:
        # Fallback: some tokens may embed roles as a list
        roles_list = payload.get("roles")
        if isinstance(roles_list, list) and len(roles_list) > 0:
            role = roles_list[0]

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing required claims (sub, role)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserContext(user_id=user_id, role=role)


# =====================================================================
# 6. ROLE-BASED ACCESS CONTROL (RBAC) DEPENDENCY FACTORY
# =====================================================================

def require_role(*roles: str) -> Callable[..., UserContext]:
    """
    Dependency factory that gates an endpoint to users holding one of
    the specified roles.

    Parameters:
        *roles: One or more role strings (e.g. ``"admin"``, ``"supervisor"``).

    Returns:
        A FastAPI dependency callable that validates the user's role.

    Raises:
        HTTPException(403): If the authenticated user's role is not
                            in the allowed set.

    Example::

        @router.delete("/machines/{machine_id}")
        def remove_machine(
            machine_id: str,
            user: UserContext = Depends(require_role("admin", "supervisor")),
        ):
            ...
    """
    allowed = set(roles)

    def _role_checker(
        user: UserContext = Depends(get_current_user),
    ) -> UserContext:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return user

    return _role_checker


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    # Database
    "get_db",
    "DBSession",
    # Auth scheme
    "oauth2_scheme",
    # Identity
    "UserContext",
    "decode_token",
    "get_current_user",
    # RBAC
    "require_role",
]
