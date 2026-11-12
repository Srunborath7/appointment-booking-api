import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.responses import app_success, app_success_paginated
from app.domain.auth import UserCreate, UserUpdate
from app.services import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    """Create a new user with specified role and details."""
    data = await user_service.create_user(payload)
    return app_success(
        msg="User created successfully",
        code=status.HTTP_201_CREATED,
        data=data,
    )


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    user_service: UserService = Depends(get_user_service),
):
    """List users with optional role, status, and search filters."""
    data, total_records, total_pages = await user_service.list_users(
        page=page,
        page_size=page_size,
        role_id=role_id,
        status_filter=status_filter,
        search=search,
    )
    return app_success_paginated(
        lists=data,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service),
):
    """Get single user by ID."""
    data = await user_service.get_user_by_id(user_id)
    return app_success(data=data)


@router.put("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """Update user profile or role."""
    data = await user_service.update_user(user_id, payload)
    return app_success(
        msg="User updated successfully",
        data=data,
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service),
):
    """Delete a user by ID."""
    await user_service.delete_user(user_id)
    return app_success(msg="User deleted successfully")
