from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.patient.model import Patient
from app.repositories.base.base_repository import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    """Repository handling database access for Patient records."""

    def __init__(self, db: AsyncSession):
        super().__init__(Patient, db)

    async def get_by_id(self, patient_id: uuid.UUID, load_user: bool = False) -> Optional[Patient]:
        """Fetch patient by ID with optional user loading."""
        stmt = select(Patient).where(Patient.id == patient_id)
        if load_user:
            stmt = stmt.options(selectinload(Patient.user))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Patient]:
        """Fetch patient associated with a specific user account ID."""
        stmt = select(Patient).where(Patient.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Patient]:
        """Fetch patient by email address."""
        stmt = select(Patient).where(Patient.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_patients(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[Patient], int]:
        """Paginated list of patients with search over names, email, and phone number."""
        stmt = select(Patient)
        count_stmt = select(func.count(Patient.id))

        if search:
            search_pattern = f"%{search}%"
            filter_expr = or_(
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.email.ilike(search_pattern),
                Patient.phone_number.ilike(search_pattern),
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        total_records = (await self.db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Patient.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        patients = list(result.scalars().all())

        return patients, total_records
