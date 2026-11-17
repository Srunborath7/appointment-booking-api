from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.room.model import Room
from app.domain.room.schema import RoomCreate, RoomResponse, RoomUpdate
from app.repositories.room_repository import RoomRepository
from app.services.base.base_service import BaseService


class RoomService(BaseService[RoomRepository]):
    """Service handling clinic rooms, consultation suites, and department allocations."""

    def __init__(self, room_repo: RoomRepository, db: AsyncSession):
        super().__init__(repository=room_repo, db=db)
        self.room_repo = room_repo

    async def create_room(self, payload: RoomCreate) -> Dict[str, Any]:
        """Create a new room, checking room_number uniqueness."""
        existing = await self.room_repo.get_by_room_number(payload.room_number)
        if existing:
            raise ConflictError(f"Room with number '{payload.room_number}' already exists")

        room = await self.room_repo.create(
            room_number=payload.room_number,
            name=payload.name,
            room_type=payload.room_type,
            department=payload.department,
            floor=payload.floor,
            building=payload.building,
            capacity=payload.capacity,
            status=payload.status,
            description=payload.description,
            is_active=payload.is_active,
        )
        return RoomResponse.model_validate(room).model_dump(mode="json")

    async def get_room_by_id(self, room_id: uuid.UUID) -> Dict[str, Any]:
        """Fetch room by ID."""
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise NotFoundError(f"Room with id '{room_id}' not found")
        return RoomResponse.model_validate(room).model_dump(mode="json")

    async def list_rooms(
        self,
        page: int = 1,
        page_size: int = 20,
        department: Optional[str] = None,
        room_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """List rooms with pagination and filters."""
        rooms, total_records = await self.room_repo.list_rooms(
            page=page,
            page_size=page_size,
            department=department,
            room_type=room_type,
            status=status,
            search=search,
        )

        total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 0
        data = [RoomResponse.model_validate(r).model_dump(mode="json") for r in rooms]
        return data, total_records, total_pages

    async def update_room(self, room_id: uuid.UUID, payload: RoomUpdate) -> Dict[str, Any]:
        """Update room metadata."""
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise NotFoundError(f"Room with id '{room_id}' not found")

        update_dict = payload.model_dump(exclude_unset=True)

        if "room_number" in update_dict and update_dict["room_number"] != room.room_number:
            existing = await self.room_repo.get_by_room_number(update_dict["room_number"])
            if existing and existing.id != room.id:
                raise ConflictError(f"Room with number '{update_dict['room_number']}' already exists")

        updated = await self.room_repo.update(room, update_dict)
        return RoomResponse.model_validate(updated).model_dump(mode="json")

    async def delete_room(self, room_id: uuid.UUID) -> bool:
        """Delete room record."""
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise NotFoundError(f"Room with id '{room_id}' not found")
        return await self.room_repo.delete(room_id)
