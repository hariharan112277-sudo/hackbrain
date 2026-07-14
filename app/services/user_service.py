"""
User management service.

Phase 4 ships with an in-memory user store keyed by user id, matching the
Member 1 storage scope.
"""
from typing import List, Dict, Any
import uuid

from app.schemas.users import UserCreate, UserUpdate
from app.core.exceptions import ResourceNotFoundError, AppBaseException


class UserService:
    """Business service for user lifecycle operations."""

    def __init__(self):
        # Simulated database store matching Member 1 storage scope
        self._users: Dict[str, Dict[str, Any]] = {
            "u1": {
                "id": "u1",
                "username": "admin",
                "email": "admin@iob.corp",
                "roles": ["admin"],
                "is_active": True,
            }
        }

    async def list_users(self) -> List[Dict[str, Any]]:
        """Return all user records."""
        return list(self._users.values())

    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Return a single user by id or raise ResourceNotFoundError."""
        user = self._users.get(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)
        return user

    async def create_user(self, user_in: UserCreate) -> Dict[str, Any]:
        """Create a new user account."""
        for u in self._users.values():
            if u["username"] == user_in.username:
                raise AppBaseException("Username already exists.", status_code=400)

        new_id = str(uuid.uuid4())
        new_user = {
            "id": new_id,
            "username": user_in.username,
            "email": user_in.email,
            "roles": user_in.roles,
            "is_active": True,
        }
        self._users[new_id] = new_user
        return new_user

    async def update_user(self, user_id: str, user_in: UserUpdate) -> Dict[str, Any]:
        """Update an existing user account."""
        user = await self.get_user_by_id(user_id)
        if user_in.email:
            user["email"] = user_in.email
        if user_in.roles:
            user["roles"] = user_in.roles
        return user

    async def delete_user(self, user_id: str) -> None:
        """Delete a user account."""
        if user_id not in self._users:
            raise ResourceNotFoundError("User", user_id)
        del self._users[user_id]
