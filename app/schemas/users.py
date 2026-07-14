"""
User Management Schemas
Phase 5: User, role, and permission models for RBAC.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class UserBase(BaseModel):
    """Base user fields."""
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    is_active: bool = Field(default=True, description="Account active status")
    roles: List[str] = Field(default=[], description="Assigned roles")


class UserCreate(UserBase):
    """User creation request."""
    password: str = Field(..., min_length=12, max_length=128, description="Initial password")


class UserUpdate(BaseModel):
    """User update request."""
    email: Optional[EmailStr] = Field(default=None, description="User email")
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = Field(default=None)
    roles: Optional[List[str]] = Field(default=None)


class UserResponse(UserBase):
    """User response model."""
    id: UUID = Field(..., description="Unique user identifier")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages")


class RoleBase(BaseModel):
    """Base role fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(default=None, max_length=500)
    permissions: List[str] = Field(default=[], description="Assigned permissions")


class RoleCreate(RoleBase):
    """Role creation request."""
    pass


class RoleUpdate(BaseModel):
    """Role update request."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    permissions: Optional[List[str]] = Field(default=None)


class RoleResponse(RoleBase):
    """Role response model."""
    id: UUID = Field(..., description="Unique role identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_system: bool = Field(default=False, description="System role flag")

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    """Base permission fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Permission name")
    resource: str = Field(..., min_length=1, max_length=100, description="Resource name")
    action: str = Field(..., min_length=1, max_length=50, description="Action (read/write/delete)")
    description: Optional[str] = Field(default=None, max_length=500)


class PermissionCreate(PermissionBase):
    """Permission creation request."""
    pass


class PermissionResponse(PermissionBase):
    """Permission response model."""
    id: UUID = Field(..., description="Unique permission identifier")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True