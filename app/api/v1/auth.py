from fastapi import APIRouter, Depends, status

from app.core.auth import get_current_user
from app.core.responses import app_success
from app.domain.auth import User, UserCreate, UserLogin
from app.services import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    result = await auth_service.register(payload)
    return app_success(
        msg="User registered successfully",
        code=status.HTTP_201_CREATED,
        data=result,
    )


@router.post("/login")
async def login(
    payload: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password."""
    result = await auth_service.login(payload)
    return app_success(
        msg="Login successful",
        data=result,
    )


@router.post("/refresh")
async def refresh_token_endpoint(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Obtain a new access token using a valid refresh token."""
    result = await auth_service.refresh_token(refresh_token)
    return app_success(
        msg="Token refreshed successfully",
        data=result,
    )


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get the authenticated user's profile."""
    result = await auth_service.get_my_profile(current_user)
    return app_success(data=result)
