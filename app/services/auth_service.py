"""
Authentication service.

Encapsulates password verification and JWT issuance. The in-memory mock identity
provider allows the framework to run immediately without an external user store.
"""
from datetime import timedelta
from typing import Dict, Any

from app.core.security import verify_password, create_access_token
from app.core.exceptions import AuthenticationError


class AuthService:
    """Business service for authenticating identities and minting tokens."""

    def __init__(self):
        # In-memory mock identity provider for core services framework
        self.mock_user_db = {
            "admin": {
                "id": "u1",
                "username": "admin",
                # Argon2 hash of "SecurePass123!"
                "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$FKI0ppRSKqXUupdy7h0jpA$wYjhc+rNfgjo969OXpewXS431cKY2c/WQpJJKgW/Y2k",
                "roles": ["admin", "operator"],
                "is_active": True,
            }
        }

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Validate credentials and return the user record on success."""
        user = self.mock_user_db.get(username)
        if not user or not verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid username or password credentials.")
        return user

    async def generate_auth_tokens(self, user: Dict[str, Any]) -> Dict[str, str]:
        """Mint access and refresh tokens for an authenticated user."""
        access_token = create_access_token(
            data={"sub": user["username"], "roles": user["roles"]},
            expires_delta=timedelta(minutes=30),
        )
        refresh_token = create_access_token(
            data={"sub": user["username"], "action": "refresh"},
            expires_delta=timedelta(days=7),
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
