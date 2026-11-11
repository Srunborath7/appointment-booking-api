import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enum import AdminStatus, ClientSurface


# Base Schema Configuration
class CustomBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# Permission Schemas
class PermissionBase(CustomBaseModel):
    codename: str = Field(..., description="Unique permission identifier, e.g. user.create")
    name: str = Field(..., description="Human-readable permission name")
    group: str = Field(..., description="Logical grouping, e.g. User Management")


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    id: uuid.UUID
    created_at: datetime


# Role Schemas
class RoleBase(CustomBaseModel):
    name: str = Field(..., description="Unique role name, e.g. admin")
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: Optional[List[uuid.UUID]] = []


class RoleResponse(RoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# User & Auth Schemas
class UserBase(CustomBaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    status: AdminStatus = AdminStatus.active
    surface: ClientSurface = ClientSurface.PORTAL


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role_id: Optional[uuid.UUID] = None


class UserUpdate(CustomBaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    status: Optional[AdminStatus] = None
    role_id: Optional[uuid.UUID] = None
    password: Optional[str] = Field(None, min_length=6)


class UserLogin(CustomBaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    role_id: Optional[uuid.UUID] = None
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    role: Optional[RoleResponse] = None


class TokenResponse(CustomBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
