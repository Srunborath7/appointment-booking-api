from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.responses import app_success
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
    JWTError,
)
from app.domain.auth import Role, User, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if email is already taken
    existing_stmt = select(User).where(User.email == payload.email)
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise ConflictError(f"Email '{payload.email}' is already registered")

    # If role_id is provided, verify it exists; else assign default 'student' or first role
    role_id = payload.role_id
    if role_id:
        role_stmt = select(Role).where(Role.id == role_id)
        role_res = await db.execute(role_stmt)
        if not role_res.scalar_one_or_none():
            raise NotFoundError("Specified role does not exist")
    else:
        # Default role: student or customer
        default_role_stmt = select(Role).where(Role.name.in_(["student", "customer", "user"]))
        default_role_res = await db.execute(default_role_stmt)
        default_role = default_role_res.scalar_one_or_none()
        if default_role:
            role_id = default_role.id

    new_user = User(
        email=payload.email,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        hashed_password=hash_password(payload.password),
        role_id=role_id,
        status=payload.status.value,
        surface=payload.surface.value,
        is_verified=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Load role relationship for response
    user_stmt = select(User).options(selectinload(User.role)).where(User.id == new_user.id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one()

    # Generate tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.name if user.role else None}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user_data = UserResponse.model_validate(user).model_dump(mode="json")
    return app_success(
        msg="User registered successfully",
        code=status.HTTP_201_CREATED,
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data,
        },
    )


@router.post("/login")
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password."""
    stmt = select(User).options(selectinload(User.role)).where(User.email == payload.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    if user.status != "active":
        raise AuthenticationError("Account is inactive or suspended")

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.name if user.role else None}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user_data = UserResponse.model_validate(user).model_dump(mode="json")
    return app_success(
        msg="Login successful",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data,
        },
    )


@router.post("/refresh")
async def refresh_token_endpoint(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Obtain a new access token using a valid refresh token."""
    try:
        payload = verify_refresh_token(refresh_token)
    except JWTError as e:
        raise AuthenticationError(f"Invalid refresh token: {str(e)}")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Token missing user subject")

    stmt = select(User).options(selectinload(User.role)).where(User.id == uuid.UUID(user_id_str))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or user.status != "active":
        raise AuthenticationError("User is no longer active")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.name if user.role else None}
    new_access_token = create_access_token(token_data)

    return app_success(
        msg="Token refreshed successfully",
        data={"access_token": new_access_token, "token_type": "bearer"},
    )


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the authenticated user's profile."""
    user_data = UserResponse.model_validate(current_user).model_dump(mode="json")
    return app_success(data=user_data)
