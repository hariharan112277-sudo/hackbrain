"""
User management REST controller.
"""
from typing import List
from fastapi import APIRouter, Depends, status

from app.schemas.users import UserResponse, UserCreate, UserUpdate
from app.services.user_service import UserService
from app.core.dependencies import get_current_user, RoleChecker

router = APIRouter(prefix="/users", tags=["Users"])
user_service = UserService()

admin_only = Depends(RoleChecker(["admin"]))


@router.get("", response_model=List[UserResponse], dependencies=[admin_only])
async def read_users():
    """List all user accounts (admin only)."""
    return await user_service.list_users()


@router.post(
    "", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[admin_only]
)
async def create_new_user(payload: UserCreate):
    """Create a new user account (admin only)."""
    return await user_service.create_user(payload)


@router.get("/{id}", response_model=UserResponse)
async def read_user(id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve a single user by id."""
    return await user_service.get_user_by_id(id)


@router.patch("/{id}", response_model=UserResponse, dependencies=[admin_only])
async def update_user(id: str, payload: UserUpdate):
    """Update a user account (admin only)."""
    return await user_service.update_user(id, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_only])
async def delete_user(id: str):
    """Delete a user account (admin only)."""
    await user_service.delete_user(id)
    return None
