"""
User management request/response schemas.
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Common user fields."""

    username: str
    email: EmailStr
    roles: List[str] = Field(default_factory=lambda: ["operator"])


class UserCreate(UserBase):
    """Payload used to create a new user account."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Payload used to update an existing user account (all fields optional)."""

    email: Optional[EmailStr] = None
    roles: Optional[List[str]] = None


class UserResponse(UserBase):
    """User record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool = True
