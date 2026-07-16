"""Persistent and policy-backed repository adapters used outside stub mode.

The user adapter maps the repository contract onto the project's frozen
``users`` SQLAlchemy table. Role and permission data are immutable application
policy because the frozen database contract does not define role or permission
tables; mutation methods therefore fail explicitly instead of silently storing
production authorization state in process memory.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import or_
from sqlalchemy.orm import Session, sessionmaker

from app.models.user import User
from app.repositories.interfaces import IPermissionRepository, IRoleRepository, IUserRepository

_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin": ["*"],
    "manager": [
        "machines:read",
        "machines:write",
        "telemetry:read",
        "alarms:read",
        "alarms:acknowledge",
        "dashboard:read",
    ],
    "engineer": [
        "machines:read",
        "machines:write",
        "telemetry:read",
        "alarms:read",
        "alarms:acknowledge",
        "alarms:resolve",
        "dashboard:read",
    ],
    "operator": ["machines:read", "telemetry:read", "alarms:read", "dashboard:read"],
    "viewer": ["machines:read", "telemetry:read", "alarms:read", "dashboard:read"],
}

_PERMISSION_DESCRIPTIONS: Dict[str, str] = {
    "machines:read": "Read machine registry data",
    "machines:write": "Create and update machine registry data",
    "machines:delete": "Delete machine registry data",
    "telemetry:read": "Read live and historical telemetry",
    "alarms:read": "Read alarm data",
    "alarms:acknowledge": "Acknowledge active alarms",
    "alarms:resolve": "Resolve active alarms",
    "dashboard:read": "Read operational dashboard data",
    "ai:predict": "Request AI predictions",
}

_POLICY_CREATED_AT = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _policy_uuid(kind: str, name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"iob-policy:{kind}:{name}")


def _permissions_for_role(role: str) -> List[str]:
    return list(_ROLE_PERMISSIONS.get(role, []))


class SQLAlchemyUserRepository(IUserRepository):
    """Async contract adapter around the synchronous frozen users table."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    @staticmethod
    def _serialize(user: User) -> Dict[str, Any]:
        created_at = user.created_at or datetime.now(timezone.utc)
        role = user.role or "viewer"
        return {
            "id": user.user_id,
            "email": user.email,
            "full_name": user.full_name or "",
            "password_hash": user.password_hash,
            "is_active": True,
            "roles": [role],
            "permissions": _permissions_for_role(role),
            "created_at": created_at,
            "updated_at": created_at,
            "last_login": None,
        }

    def _run(self, operation):
        session = self._session_factory()
        try:
            return operation(session)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        def operation(session: Session) -> Optional[Dict[str, Any]]:
            try:
                normalized_id = UUID(str(user_id))
            except (TypeError, ValueError):
                return None
            user = session.query(User).filter(User.user_id == normalized_id).first()
            return self._serialize(user) if user else None

        return await asyncio.to_thread(self._run, operation)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        def operation(session: Session) -> Optional[Dict[str, Any]]:
            user = session.query(User).filter(User.email == str(email)).first()
            return self._serialize(user) if user else None

        return await asyncio.to_thread(self._run, operation)

    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        def operation(session: Session) -> tuple[List[Dict[str, Any]], int]:
            query = session.query(User)
            active_filters = filters or {}
            search = active_filters.get("search")
            if search:
                pattern = f"%{search}%"
                query = query.filter(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
            role = active_filters.get("role")
            if role:
                query = query.filter(User.role == role)
            if active_filters.get("is_active") is False:
                return [], 0
            total = query.count()
            rows = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
            return [self._serialize(row) for row in rows], total

        return await asyncio.to_thread(self._run, operation)

    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        def operation(session: Session) -> Dict[str, Any]:
            requested_id = user_data.get("id")
            try:
                normalized_id = UUID(str(requested_id)) if requested_id is not None else uuid4()
            except (TypeError, ValueError):
                normalized_id = uuid4()
            if normalized_id.int == 0:
                normalized_id = uuid4()

            roles = user_data.get("roles") or [user_data.get("role") or "viewer"]
            user = User(
                user_id=normalized_id,
                email=str(user_data["email"]),
                full_name=user_data.get("full_name"),
                password_hash=str(user_data["password_hash"]),
                role=str(roles[0]),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return self._serialize(user)

        return await asyncio.to_thread(self._run, operation)

    async def update(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        def operation(session: Session) -> Dict[str, Any]:
            user = session.query(User).filter(User.user_id == UUID(str(user_id))).first()
            if user is None:
                raise LookupError(f"User {user_id} no longer exists")
            if "email" in updates:
                user.email = str(updates["email"])
            if "full_name" in updates:
                user.full_name = updates["full_name"]
            if "roles" in updates and updates["roles"]:
                user.role = str(updates["roles"][0])
            if "role" in updates and updates["role"]:
                user.role = str(updates["role"])
            session.commit()
            session.refresh(user)
            return self._serialize(user)

        return await asyncio.to_thread(self._run, operation)

    async def delete(self, user_id: str) -> bool:
        def operation(session: Session) -> bool:
            user = session.query(User).filter(User.user_id == UUID(str(user_id))).first()
            if user is None:
                return False
            session.delete(user)
            session.commit()
            return True

        return await asyncio.to_thread(self._run, operation)

    async def update_last_login(self, user_id: str) -> None:
        # The frozen users table has no last_login column. Verify the subject
        # exists so callers still receive a deterministic failure for stale IDs.
        if await self.get_by_id(user_id) is None:
            raise LookupError(f"User {user_id} no longer exists")

    async def update_password(self, user_id: str, password_hash: str) -> None:
        def operation(session: Session) -> None:
            user = session.query(User).filter(User.user_id == UUID(str(user_id))).first()
            if user is None:
                raise LookupError(f"User {user_id} no longer exists")
            user.password_hash = password_hash
            session.commit()

        await asyncio.to_thread(self._run, operation)


class PolicyRoleRepository(IRoleRepository):
    """Read-only role policy matching the frozen single-role users schema."""

    @staticmethod
    def _serialize(name: str) -> Dict[str, Any]:
        return {
            "id": _policy_uuid("role", name),
            "name": name,
            "description": f"Built-in {name} role",
            "permissions": _permissions_for_role(name),
            "created_at": _POLICY_CREATED_AT,
            "is_system": True,
        }

    async def get_by_id(self, role_id: str) -> Optional[Dict[str, Any]]:
        return next(
            (
                self._serialize(name)
                for name in _ROLE_PERMISSIONS
                if _policy_uuid("role", name) == UUID(str(role_id))
            ),
            None,
        )

    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return self._serialize(name) if name in _ROLE_PERMISSIONS else None

    async def list_roles(self) -> List[Dict[str, Any]]:
        return [self._serialize(name) for name in _ROLE_PERMISSIONS]

    async def create(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("Role policy is immutable without a role-table migration")

    async def update(self, role_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("Role policy is immutable without a role-table migration")

    async def delete(self, role_id: str) -> bool:
        raise RuntimeError("System role policy cannot be deleted")


class PolicyPermissionRepository(IPermissionRepository):
    """Read-only permission catalogue for the built-in role policy."""

    @staticmethod
    def _serialize(name: str) -> Dict[str, Any]:
        resource, action = name.split(":", maxsplit=1)
        return {
            "id": _policy_uuid("permission", name),
            "name": name,
            "resource": resource,
            "action": action,
            "description": _PERMISSION_DESCRIPTIONS[name],
            "created_at": _POLICY_CREATED_AT,
        }

    async def get_by_id(self, perm_id: str) -> Optional[Dict[str, Any]]:
        return next(
            (
                self._serialize(name)
                for name in _PERMISSION_DESCRIPTIONS
                if _policy_uuid("permission", name) == UUID(str(perm_id))
            ),
            None,
        )

    async def list_permissions(self) -> List[Dict[str, Any]]:
        return [self._serialize(name) for name in _PERMISSION_DESCRIPTIONS]

    async def create(self, perm_data: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("Permission policy is immutable without a permission-table migration")

    async def update(self, perm_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("Permission policy is immutable without a permission-table migration")

    async def delete(self, perm_id: str) -> bool:
        raise RuntimeError("System permission policy cannot be deleted")


__all__ = [
    "PolicyPermissionRepository",
    "PolicyRoleRepository",
    "SQLAlchemyUserRepository",
]
