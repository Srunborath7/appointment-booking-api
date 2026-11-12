from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.patient.model import Patient
from app.domain.patient.schema import PatientCreate, PatientResponse, PatientUpdate
from app.repositories.auth_repository import AuthRepository
from app.repositories.patient_repository import PatientRepository
from app.services.base.base_service import BaseService


class PatientService(BaseService[PatientRepository]):
    """Service handling patient profile lifecycle, health records metadata, and patient registration."""

    def __init__(
        self,
        patient_repo: PatientRepository,
        auth_repo: AuthRepository,
        db: AsyncSession,
    ):
        super().__init__(repository=patient_repo, db=db)
        self.patient_repo = patient_repo
        self.auth_repo = auth_repo

    async def create_patient(self, payload: PatientCreate) -> Dict[str, Any]:
        """Create a new patient record."""
        # 1. Validate user_id if attached
        if payload.user_id:
            user = await self.auth_repo.get_by_id(payload.user_id)
            if not user:
                raise NotFoundError(f"Associated user account '{payload.user_id}' does not exist")

            # Check if this user is already linked to a patient profile
            existing_for_user = await self.patient_repo.get_by_user_id(payload.user_id)
            if existing_for_user:
                raise ConflictError("A patient record is already associated with this user account")

        # 2. Check email uniqueness if email provided
        if payload.email:
            existing_email = await self.patient_repo.get_by_email(payload.email)
            if existing_email:
                raise ConflictError(f"A patient with email '{payload.email}' already exists")

        patient = await self.patient_repo.create(
            user_id=payload.user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            phone_number=payload.phone_number,
            email=payload.email,
            address=payload.address,
            blood_group=payload.blood_group,
            allergies=payload.allergies,
            medical_history=payload.medical_history,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
        )

        return PatientResponse.model_validate(patient).model_dump(mode="json")

    async def list_patients(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """List patients with pagination and search."""
        patients, total_records = await self.patient_repo.list_patients(
            page=page,
            page_size=page_size,
            search=search,
        )

        total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 0
        data = [PatientResponse.model_validate(p).model_dump(mode="json") for p in patients]
        return data, total_records, total_pages

    async def get_patient_by_id(self, patient_id: uuid.UUID) -> Dict[str, Any]:
        """Fetch patient by ID."""
        patient = await self.patient_repo.get_by_id(patient_id, load_user=True)
        if not patient:
            raise NotFoundError(f"Patient with id '{patient_id}' not found")
        return PatientResponse.model_validate(patient).model_dump(mode="json")

    async def get_patient_by_user_id(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Fetch patient associated with an authenticated user ID."""
        patient = await self.patient_repo.get_by_user_id(user_id)
        if not patient:
            raise NotFoundError("No patient record found for this user account")
        return PatientResponse.model_validate(patient).model_dump(mode="json")

    async def update_patient(
        self, patient_id: uuid.UUID, payload: PatientUpdate
    ) -> Dict[str, Any]:
        """Update existing patient details."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError(f"Patient with id '{patient_id}' not found")

        update_dict = payload.model_dump(exclude_unset=True)

        # If email is being updated, verify it doesn't conflict
        if "email" in update_dict and update_dict["email"] and update_dict["email"] != patient.email:
            existing = await self.patient_repo.get_by_email(update_dict["email"])
            if existing and existing.id != patient.id:
                raise ConflictError(f"Email '{update_dict['email']}' is already in use by another patient")

        updated = await self.patient_repo.update(patient, update_dict)
        return PatientResponse.model_validate(updated).model_dump(mode="json")

    async def delete_patient(self, patient_id: uuid.UUID) -> bool:
        """Delete patient record."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError(f"Patient with id '{patient_id}' not found")
        return await self.patient_repo.delete(patient_id)
