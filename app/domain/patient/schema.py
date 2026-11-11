import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PatientBase(CustomBaseModel):
    first_name: str = Field(..., max_length=100, description="Patient's first name")
    last_name: str = Field(..., max_length=100, description="Patient's last name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, max_length=20, description="Gender (male, female, other)")
    phone_number: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Contact email address")
    address: Optional[str] = Field(None, description="Residential address")
    blood_group: Optional[str] = Field(None, max_length=10, description="Blood type, e.g. A+, O-")
    allergies: Optional[str] = Field(None, description="Known drug/food allergies")
    medical_history: Optional[str] = Field(None, description="Pre-existing medical conditions or notes")
    emergency_contact_name: Optional[str] = Field(None, max_length=150, description="Emergency contact person")
    emergency_contact_phone: Optional[str] = Field(None, max_length=50, description="Emergency contact phone number")


class PatientCreate(PatientBase):
    user_id: Optional[uuid.UUID] = Field(None, description="Associated user ID if patient has login account")


class PatientUpdate(CustomBaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    phone_number: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    blood_group: Optional[str] = Field(None, max_length=10)
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=150)
    emergency_contact_phone: Optional[str] = Field(None, max_length=50)


class PatientResponse(PatientBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
