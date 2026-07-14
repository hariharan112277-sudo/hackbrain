"""
Authentication REST controller.
"""
from fastapi import APIRouter, Depends, status

from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    """Authenticate with username/password and return JWT tokens."""
    user = await auth_service.authenticate_user(payload.username, payload.password)
    tokens = await auth_service.generate_auth_tokens(user)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    """Obtain a new access token using a valid refresh token."""
    from app.core.security import decode_access_token

    payload_data = decode_access_token(payload.refresh_token)
    if not payload_data or payload_data.get("action") != "refresh":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    user = auth_service.mock_user_db.get(payload_data["sub"])
    if not user:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    tokens = await auth_service.generate_auth_tokens(user)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint.

    Tokens are typically invalidated on client side or added to blocklists in DB setup.
    """
    return None
