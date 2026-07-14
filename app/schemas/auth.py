"""
Authentication Schemas
Phase 5: JWT token and authentication request/response models.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator


class Token(BaseModel):
    """JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class TokenData(BaseModel):
    """Decoded token payload."""
    sub: str = Field(..., description="Subject (user ID)")
    email: EmailStr = Field(..., description="User email")
    roles: List[str] = Field(default=[], description="User roles")
    permissions: List[str] = Field(default=[], description="User permissions")
    exp: datetime = Field(..., description="Expiration time")
    type: str = Field(..., description="Token type (access/refresh)")


class LoginRequest(BaseModel):
    """Login request payload."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Extend token expiry")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="JWT refresh token")


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=12, max_length=128, description="Password")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    role: Optional[str] = Field(default="operator", description="Initial role")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=12, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for v):
            raise ValueError("Password must contain at least one special character")
        return v


class AuthResponse(BaseModel):
    """Generic auth response."""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Response message")
    data: Optional[Token] = Field(default=None, description="Token data if applicable")