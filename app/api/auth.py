"""
Authentication API Routes
Phase 5: Login, register, token refresh, password change endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.core.security import get_current_user, get_current_user_id
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    PasswordChangeRequest,
    Token,
    AuthResponse,
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_auth_service

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=Token, summary="User login")
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return access/refresh tokens."""
    return await auth_service.authenticate_user(login_data)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, summary="User registration")
async def register(
    register_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user and return tokens."""
    return await auth_service.register_user(register_data)


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    return await auth_service.refresh_access_token(refresh_data.refresh_token)


@router.post("/change-password", response_model=AuthResponse, summary="Change password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change current user's password."""
    from uuid import UUID
    await auth_service.change_password(
        user_id=UUID(current_user_id),
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )
    return AuthResponse(success=True, message="Password changed successfully")


@router.get("/me", summary="Get current user info")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "roles": current_user.get("roles", []),
        "permissions": current_user.get("permissions", []),
    }


@router.post("/logout", response_model=AuthResponse, summary="User logout")
async def logout(
    current_user_id: str = Depends(get_current_user_id),
):
    """Logout user (client-side token invalidation)."""
    # In a production system, you might want to blacklist the token
    # For now, we just return success - client should delete tokens
    return AuthResponse(success=True, message="Logged out successfully")