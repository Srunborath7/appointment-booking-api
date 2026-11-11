import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.responses import app_success, app_success_paginated
from app.core.security import hash_password
from app.domain.auth import Role, User, UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user with specified role and details."""
    # Check if email is already taken
    existing_stmt = select(User).where(User.email == payload.email)
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise ConflictError(f"Email '{payload.email}' is already registered")

    # Verify role exists if supplied
    if payload.role_id:
        role_stmt = select(Role).where(Role.id == payload.role_id)
        role_res = await db.execute(role_stmt)
        if not role_res.scalar_one_or_none():
            raise NotFoundError(f"Role with id '{payload.role_id}' not found")

    new_user = User(
        email=payload.email,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        hashed_password=hash_password(payload.password),
        role_id=payload.role_id,
        status=payload.status.value,
        surface=payload.surface.value,
        is_verified=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Load with role
    stmt = select(User).options(selectinload(User.role)).where(User.id == new_user.id)
    res = await db.execute(stmt)
    created = res.scalar_one()

    return app_success(
        msg="User created successfully",
        code=status.HTTP_201_CREATED,
        data=UserResponse.model_validate(created).model_dump(mode="json"),
    )


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List users with optional role, status, and search filters."""
    stmt = select(User).options(selectinload(User.role))

    if role_id:
        stmt = stmt.where(User.role_id == role_id)
    if status_filter:
        stmt = stmt.where(User.status == status_filter)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where((User.full_name.ilike(search_filter)) | (User.email.ilike(search_filter)))

    # Count total
    count_stmt = select(func.count(User.id))
    if role_id:
        count_stmt = count_stmt.where(User.role_id == role_id)
    if status_filter:
        count_stmt = count_stmt.where(User.status == status_filter)
    if search:
        count_stmt = count_stmt.where(
            (User.full_name.ilike(search_filter)) | (User.email.ilike(search_filter))
        )
    total_records = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    users = (await db.execute(stmt)).scalars().all()

    total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 0
    data = [UserResponse.model_validate(u).model_dump(mode="json") for u in users]

    return app_success_paginated(
        lists=data,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )


@router.get("/{user_id}")
async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get single user by ID."""
    stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise NotFoundError(f"User with id '{user_id}' not found")
    return app_success(data=UserResponse.model_validate(user).model_dump(mode="json"))


@router.put("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update user profile or role."""
    stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise NotFoundError(f"User with id '{user_id}' not found")

    if payload.role_id is not None:
        role_stmt = select(Role).where(Role.id == payload.role_id)
        role_res = await db.execute(role_stmt)
        if not role_res.scalar_one_or_none():
            raise NotFoundError(f"Role with id '{payload.role_id}' not found")
        user.role_id = payload.role_id

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number
    if payload.status is not None:
        user.status = payload.status.value
    if payload.password:
        user.hashed_password = hash_password(payload.password)

    await db.commit()
    await db.refresh(user)

    return app_success(
        msg="User updated successfully",
        data=UserResponse.model_validate(user).model_dump(mode="json"),
    )


@router.delete("/{user_id}")
async def delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a user by ID."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise NotFoundError(f"User with id '{user_id}' not found")

    await db.delete(user)
    await db.commit()
    return app_success(msg="User deleted successfully")
