"""
Authentication & authorization request/response schemas.
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Username / password login payload."""

    username: str = Field(..., examples=["admin"])
    password: str = Field(..., min_length=8, examples=["SecurePass123!"])


class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token request body."""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Password change payload for authenticated users."""

    old_password: str
    new_password: str = Field(..., min_length=8)
