import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.responses import app_success, app_success_paginated
from app.domain.room import RoomCreate, RoomUpdate
from app.services import RoomService, get_room_service

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    room_service: RoomService = Depends(get_room_service),
):
    """Create a new clinic room or consultation suite."""
    data = await room_service.create_room(payload)
    return app_success(
        msg="Room created successfully",
        code=status.HTTP_201_CREATED,
        data=data,
    )


@router.get("")
async def list_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department: Optional[str] = Query(None),
    room_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    room_service: RoomService = Depends(get_room_service),
):
    """List rooms with optional department, room_type, status, and search filters."""
    data, total_records, total_pages = await room_service.list_rooms(
        page=page,
        page_size=page_size,
        department=department,
        room_type=room_type,
        status=status,
        search=search,
    )
    return app_success_paginated(
        lists=data,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )


@router.get("/{room_id}")
async def get_room_by_id(
    room_id: uuid.UUID,
    room_service: RoomService = Depends(get_room_service),
):
    """Get single room details by ID."""
    data = await room_service.get_room_by_id(room_id)
    return app_success(data=data)


@router.put("/{room_id}")
async def update_room(
    room_id: uuid.UUID,
    payload: RoomUpdate,
    room_service: RoomService = Depends(get_room_service),
):
    """Update room details or status."""
    data = await room_service.update_room(room_id, payload)
    return app_success(
        msg="Room updated successfully",
        data=data,
    )


@router.delete("/{room_id}")
async def delete_room(
    room_id: uuid.UUID,
    room_service: RoomService = Depends(get_room_service),
):
    """Delete a room record."""
    await room_service.delete_room(room_id)
    return app_success(msg="Room deleted successfully")
