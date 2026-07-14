"""
User Management Service
Phase 5: User CRUD operations, role and permission management.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

import structlog

from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)
from app.schemas.users import (
    UserResponse,
    UserCreate,
    UserUpdate,
    UserListResponse,
    RoleResponse,
    PermissionResponse,
)
from app.repositories.interfaces import IUserRepository, IRoleRepository, IPermissionRepository

logger = structlog.get_logger("app.services.user")


class UserService:
    """User management business logic."""

    def __init__(
        self,
        user_repo: IUserRepository,
        role_repo: IRoleRepository,
        permission_repo: IPermissionRepository,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def get_user(self, user_id: UUID) -> UserResponse:
        """Get user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        return UserResponse(**user)

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        return UserResponse(**user)

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> UserListResponse:
        """List users with pagination and filtering."""
        offset = (page - 1) * page_size
        users, total = await self.user_repo.list_users(
            limit=page_size,
            offset=offset,
            filters=filters,
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return UserListResponse(
            users=[UserResponse(**u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        # Check email uniqueness
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            raise ValidationError("Email already registered")
        
        # Validate roles exist
        if user_data.roles:
            for role_name in user_data.roles:
                role = await self.role_repo.get_by_name(role_name)
                if not role:
                    raise ValidationError(f"Role '{role_name}' does not exist")
        
        from app.core.security import get_password_hash
        
        create_data = {
            "id": UUID(int=0),  # Will be set by repo
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": get_password_hash(user_data.password),
            "is_active": user_data.is_active,
            "roles": user_data.roles,
            "permissions": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        user = await self.user_repo.create(create_data)
        logger.info("user_created", user_id=str(user["id"]), email=user["email"])
        return UserResponse(**user)

    async def update_user(self, user_id: UUID, updates: UserUpdate) -> UserResponse:
        """Update user information."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        update_data = {}
        
        if updates.email is not None:
            existing = await self.user_repo.get_by_email(updates.email)
            if existing and existing["id"] != user_id:
                raise ValidationError("Email already in use")
            update_data["email"] = updates.email
        
        if updates.full_name is not None:
            update_data["full_name"] = updates.full_name
        
        if updates.is_active is not None:
            update_data["is_active"] = updates.is_active
        
        if updates.roles is not None:
            # Validate roles exist
            for role_name in updates.roles:
                role = await self.role_repo.get_by_name(role_name)
                if not role:
                    raise ValidationError(f"Role '{role_name}' does not exist")
            update_data["roles"] = updates.roles
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        updated_user = await self.user_repo.update(user_id, update_data)
        logger.info("user_updated", user_id=str(user_id))
        return UserResponse(**updated_user)

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        await self.user_repo.delete(user_id)
        logger.info("user_deleted", user_id=str(user_id))
        return True

    async def assign_roles(self, user_id: UUID, role_names: List[str]) -> UserResponse:
        """Assign roles to user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        # Validate roles
        for role_name in role_names:
            role = await self.role_repo.get_by_name(role_name)
            if not role:
                raise ValidationError(f"Role '{role_name}' does not exist")
        
        updated = await self.user_repo.update(user_id, {"roles": role_names})
        return UserResponse(**updated)

    # Role Management
    async def create_role(self, role_data: Dict[str, Any]) -> RoleResponse:
        """Create a new role."""
        existing = await self.role_repo.get_by_name(role_data["name"])
        if existing:
            raise ValidationError("Role already exists")
        
        role = await self.role_repo.create(role_data)
        return RoleResponse(**role)

    async def get_role(self, role_id: UUID) -> RoleResponse:
        """Get role by ID."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ResourceNotFoundError("Role", str(role_id))
        return RoleResponse(**role)

    async def list_roles(self) -> List[RoleResponse]:
        """List all roles."""
        roles = await self.role_repo.list_roles()
        return [RoleResponse(**r) for r in roles]

    async def update_role(self, role_id: UUID, updates: Dict[str, Any]) -> RoleResponse:
        """Update role."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ResourceNotFoundError("Role", str(role_id))
        
        updated = await self.role_repo.update(role_id, updates)
        return RoleResponse(**updated)

    async def delete_role(self, role_id: UUID) -> bool:
        """Delete role."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ResourceNotFoundError("Role", str(role_id))
        
        if role.get("is_system"):
            raise ValidationError("Cannot delete system role")
        
        await self.role_repo.delete(role_id)
        return True

    # Permission Management
    async def create_permission(self, perm_data: Dict[str, Any]) -> PermissionResponse:
        """Create a new permission."""
        perm = await self.permission_repo.create(perm_data)
        return PermissionResponse(**perm)

    async def list_permissions(self) -> List[PermissionResponse]:
        """List all permissions."""
        perms = await self.permission_repo.list_permissions()
        return [PermissionResponse(**p) for p in perms]