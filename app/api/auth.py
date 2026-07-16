"""
Authentication API Routes — Track A (Hariharan) — Stage 2 (Authentication)
Industrial Operating Brain (IOB) Platform

Endpoints:
  POST /login   — authenticate with email + password, return tokens + profile
  POST /refresh — exchange a refresh token for a new access token
  GET  /me      — return the active session user's profile

Integrates with:
  * app.database.get_db          (Stage 1 session generator)
  * app.core.security            (Stage 2 hashing / JWT)
  * app.core.errors.error_envelope
  * app.deps.get_current_user    (Stage 0 UserContext dependency)
  * app.models.user.User         (Stage 1 ORM)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import security
from app.core.errors import error_envelope
from app.database import get_db
from app.deps import UserContext, get_current_user
from app.models.schemas import LoginRequest, RefreshRequest
from app.models.user import User

router = APIRouter()


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user.

    Returns access/refresh tokens and the parsed user profile on success.
    Throws consistent 401 errors using error_envelope on failure.
    """
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not security.verify_password(body.password, user.password_hash):
        raise error_envelope(
            "INVALID_CREDENTIALS",
            "Email or password is incorrect",
            401,
        )

    access_token = security.create_access_token(str(user.user_id), user.role)
    # Embed role in the refresh token so /refresh can re-issue a correct access token
    refresh_token = security.create_refresh_token(str(user.user_id), role=user.role)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "user_id": str(user.user_id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        },
    }


@router.post("/refresh")
def refresh(body: RefreshRequest):
    """
    Validate a refresh token and generate a brand new access token.
    """
    payload = security.decode_token(body.refresh_token)

    # Ensure this token is explicitly tagged as a refresh token
    if payload.get("type") != "refresh":
        raise error_envelope(
            "INVALID_TOKEN",
            "Provided token is not a refresh token",
            401,
        )

    user_id = payload.get("sub")
    if not user_id:
        raise error_envelope(
            "INVALID_TOKEN",
            "Refresh token is missing subject claim",
            401,
        )

    role = payload.get("role") or "viewer"
    return {
        "access_token": security.create_access_token(str(user_id), role),
    }


@router.get("/me")
def me(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return user details of the verified, active session user context.
    """
    u = db.query(User).filter(User.user_id == user.user_id).first()
    if not u:
        raise error_envelope(
            "USER_NOT_FOUND",
            "Logged-in user record does not exist in database",
            404,
        )

    return {
        "user_id": str(u.user_id),
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
    }
