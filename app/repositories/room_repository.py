from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.room.model import Room
from app.repositories.base.base_repository import BaseRepository


class RoomRepository(BaseRepository[Room]):
    """Repository handling database access for Room entities."""

    def __init__(self, db: AsyncSession):
        super().__init__(Room, db)

    async def get_by_id(self, room_id: uuid.UUID) -> Optional[Room]:
        """Fetch room by primary UUID."""
        stmt = select(Room).where(Room.id == room_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_room_number(self, room_number: str) -> Optional[Room]:
        """Fetch room by unique room number/code."""
        stmt = select(Room).where(Room.room_number == room_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rooms(
        self,
        page: int = 1,
        page_size: int = 20,
        department: Optional[str] = None,
        room_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Room], int]:
        """Paginated list of rooms with optional filtering by department, type, status, and search."""
        stmt = select(Room)
        count_stmt = select(func.count(Room.id))

        if department:
            stmt = stmt.where(Room.department == department)
            count_stmt = count_stmt.where(Room.department == department)

        if room_type:
            stmt = stmt.where(Room.room_type == room_type)
            count_stmt = count_stmt.where(Room.room_type == room_type)

        if status:
            stmt = stmt.where(Room.status == status)
            count_stmt = count_stmt.where(Room.status == status)

        if search:
            search_pattern = f"%{search}%"
            filter_expr = or_(
                Room.room_number.ilike(search_pattern),
                Room.name.ilike(search_pattern),
                Room.department.ilike(search_pattern),
                Room.building.ilike(search_pattern),
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        total_records = (await self.db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Room.room_number.asc()).offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        rooms = list(result.scalars().all())

        return rooms, total_records
