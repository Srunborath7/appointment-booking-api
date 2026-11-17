import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RoomBase(CustomBaseModel):
    room_number: str = Field(..., max_length=50, description="Unique room number or code, e.g. 'Room 101'")
    name: str = Field(..., max_length=100, description="Display name, e.g. 'Cardiology Suite A'")
    room_type: str = Field("consultation", max_length=50, description="Room type: consultation, examination, surgery, triage, dental")
    department: Optional[str] = Field(None, max_length=100, description="Clinical department")
    floor: Optional[str] = Field(None, max_length=50, description="Floor level, e.g. '1st Floor'")
    building: Optional[str] = Field(None, max_length=100, description="Building or wing name")
    capacity: int = Field(1, ge=1, description="Maximum patient capacity")
    status: str = Field("available", max_length=30, description="Status: available, occupied, maintenance, reserved")
    description: Optional[str] = Field(None, description="Equipment, facilities, or notes")
    is_active: bool = Field(True, description="Whether the room is currently active in service")


class RoomCreate(RoomBase):
    pass


class RoomUpdate(CustomBaseModel):
    room_number: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    room_type: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    floor: Optional[str] = Field(None, max_length=50)
    building: Optional[str] = Field(None, max_length=100)
    capacity: Optional[int] = Field(None, ge=1)
    status: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoomResponse(RoomBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
