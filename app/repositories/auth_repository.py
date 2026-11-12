from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.auth.model import Role, User
from app.repositories.base.base_repository import BaseRepository


class AuthRepository(BaseRepository[User]):
    """Repository handling database access for User and authentication entities."""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str, load_role: bool = True) -> Optional[User]:
        """Fetch user by unique email with optional eager loading of role."""
        stmt = select(User).where(User.email == email)
        if load_role:
            stmt = stmt.options(selectinload(User.role))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID, load_role: bool = True) -> Optional[User]:
        """Fetch user by UUID with optional eager loading of role."""
        stmt = select(User).where(User.id == user_id)
        if load_role:
            stmt = stmt.options(selectinload(User.role))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_patient(self, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user with both role and patient relationship loaded."""
        stmt = (
            select(User)
            .options(selectinload(User.role), selectinload(User.patient))
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_login(self, user: User) -> User:
        """Update last login timestamp to now."""
        user.last_login_at = datetime.now(timezone.utc)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[User], int]:
        """Paginated list of users with optional filtering."""
        stmt = select(User).options(selectinload(User.role))
        count_stmt = select(func.count(User.id))

        if role_id:
            stmt = stmt.where(User.role_id == role_id)
            count_stmt = count_stmt.where(User.role_id == role_id)
        if status_filter:
            stmt = stmt.where(User.status == status_filter)
            count_stmt = count_stmt.where(User.status == status_filter)
        if search:
            search_pattern = f"%{search}%"
            filter_expr = or_(
                User.full_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.phone_number.ilike(search_pattern),
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        total_records = (await self.db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        users = list(result.scalars().all())

        return users, total_records
