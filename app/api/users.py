"""
User Management API Routes
Phase 5: User CRUD, role and permission management endpoints.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_user, require_roles, require_permissions
from app.schemas.users import (
    UserResponse,
    UserCreate,
    UserUpdate,
    UserListResponse,
    RoleResponse,
    RoleCreate,
    RoleUpdate,
    PermissionResponse,
    PermissionCreate,
)
from app.services.user_service import UserService
from app.core.dependencies import get_user_service

router = APIRouter()


# User Routes
@router.get("", response_model=UserListResponse, summary="List users")
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search term"),
    role: str = Query(None, description="Filter by role"),
    is_active: bool = Query(None, description="Filter by active status"),
    current_user: dict = Depends(require_roles("admin", "manager")),
    user_service: UserService = Depends(get_user_service),
):
    """List users with pagination and filtering (admin/manager only)."""
    filters = {}
    if search:
        filters["search"] = search
    if role:
        filters["role"] = role
    if is_active is not None:
        filters["is_active"] = is_active
    
    return await user_service.list_users(page=page, page_size=page_size, filters=filters)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(require_roles("admin", "manager")),
    user_service: UserService = Depends(get_user_service),
):
    """Get user by ID (admin/manager only)."""
    return await user_service.get_user(user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create user")
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Create a new user (admin only)."""
    return await user_service.create_user(user_data)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Update user information (admin only)."""
    return await user_service.update_user(user_id, updates)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(
    user_id: UUID,
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Delete a user (admin only)."""
    await user_service.delete_user(user_id)


@router.post("/{user_id}/roles", response_model=UserResponse, summary="Assign roles to user")
async def assign_user_roles(
    user_id: UUID,
    role_names: List[str],
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Assign roles to a user (admin only)."""
    return await user_service.assign_roles(user_id, role_names)


# Role Routes
@router.get("/roles/", response_model=List[RoleResponse], summary="List all roles")
async def list_roles(
    current_user: dict = Depends(require_roles("admin", "manager")),
    user_service: UserService = Depends(get_user_service),
):
    """List all roles (admin/manager only)."""
    return await user_service.list_roles()


@router.get("/roles/{role_id}", response_model=RoleResponse, summary="Get role by ID")
async def get_role(
    role_id: UUID,
    current_user: dict = Depends(require_roles("admin", "manager")),
    user_service: UserService = Depends(get_user_service),
):
    """Get role by ID (admin/manager only)."""
    return await user_service.get_role(role_id)


@router.post("/roles/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="Create role")
async def create_role(
    role_data: RoleCreate,
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Create a new role (admin only)."""
    return await user_service.create_role(role_data.model_dump())


@router.patch("/roles/{role_id}", response_model=RoleResponse, summary="Update role")
async def update_role(
    role_id: UUID,
    updates: RoleUpdate,
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Update a role (admin only)."""
    return await user_service.update_role(role_id, updates.model_dump(exclude_unset=True))


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete role")
async def delete_role(
    role_id: UUID,
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Delete a role (admin only)."""
    await user_service.delete_role(role_id)


# Permission Routes
@router.get("/permissions/", response_model=List[PermissionResponse], summary="List all permissions")
async def list_permissions(
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """List all permissions (admin only)."""
    return await user_service.list_permissions()


@router.post("/permissions/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED, summary="Create permission")
async def create_permission(
    perm_data: PermissionCreate,
    current_user: dict = Depends(require_roles("admin")),
    user_service: UserService = Depends(get_user_service),
):
    """Create a new permission (admin only)."""
    return await user_service.create_permission(perm_data.model_dump())