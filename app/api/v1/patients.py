import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.auth import get_current_user
from app.core.responses import app_success, app_success_paginated
from app.domain.auth.model import User
from app.domain.patient.schema import PatientCreate, PatientUpdate
from app.services import PatientService, get_patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_patient(
    payload: PatientCreate,
    patient_service: PatientService = Depends(get_patient_service),
):
    """Create a new patient record."""
    data = await patient_service.create_patient(payload)
    return app_success(
        msg="Patient created successfully",
        code=status.HTTP_201_CREATED,
        data=data,
    )


@router.get("")
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    patient_service: PatientService = Depends(get_patient_service),
):
    """List patients with optional search filter."""
    data, total_records, total_pages = await patient_service.list_patients(
        page=page,
        page_size=page_size,
        search=search,
    )
    return app_success_paginated(
        lists=data,
        total_records=total_records,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )


@router.get("/me")
async def get_my_patient_profile(
    current_user: User = Depends(get_current_user),
    patient_service: PatientService = Depends(get_patient_service),
):
    """Fetch the patient profile associated with currently authenticated user."""
    data = await patient_service.get_patient_by_user_id(current_user.id)
    return app_success(data=data)


@router.get("/{patient_id}")
async def get_patient_by_id(
    patient_id: uuid.UUID,
    patient_service: PatientService = Depends(get_patient_service),
):
    """Get single patient by ID."""
    data = await patient_service.get_patient_by_id(patient_id)
    return app_success(data=data)


@router.put("/{patient_id}")
async def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    patient_service: PatientService = Depends(get_patient_service),
):
    """Update patient details."""
    data = await patient_service.update_patient(patient_id, payload)
    return app_success(
        msg="Patient updated successfully",
        data=data,
    )


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: uuid.UUID,
    patient_service: PatientService = Depends(get_patient_service),
):
    """Delete patient record."""
    await patient_service.delete_patient(patient_id)
    return app_success(msg="Patient deleted successfully")
