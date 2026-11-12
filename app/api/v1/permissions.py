import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.responses import app_success
from app.domain.auth import PermissionCreate
from app.services import RoleService, get_role_service

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_permission(
    payload: PermissionCreate,
    role_service: RoleService = Depends(get_role_service),
):
    """Create a new permission definition."""
    data = await role_service.create_permission(payload)
    return app_success(
        msg="Permission created successfully",
        code=status.HTTP_201_CREATED,
        data=data,
    )


@router.get("")
async def list_permissions(
    group: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    role_service: RoleService = Depends(get_role_service),
):
    """List all available permissions with optional group and search filters."""
    data = await role_service.list_permissions(group=group, search=search)
    return app_success(data=data)


@router.get("/{permission_id}")
async def get_permission_by_id(
    permission_id: uuid.UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """Get single permission details."""
    data = await role_service.get_permission_by_id(permission_id)
    return app_success(data=data)


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: uuid.UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """Delete a permission by ID."""
    await role_service.delete_permission(permission_id)
    return app_success(msg="Permission deleted successfully")


@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_system_permissions(
    role_service: RoleService = Depends(get_role_service),
):
    """Seed initial system permission catalog."""
    await role_service.seed_system_permissions()
    return app_success(msg="System permissions seeded successfully")
