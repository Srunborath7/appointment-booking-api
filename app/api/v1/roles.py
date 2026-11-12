from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, status

from app.core.responses import app_success
from app.domain.auth import RoleCreate
from app.services import RoleService, get_role_service

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
):
    """Create a new role with optional permission assignments."""
    data = await role_service.create_role(payload)
    return app_success(
        msg="Role created successfully",
        code=status.HTTP_201_CREATED,
        data=data,
    )


@router.get("")
async def list_roles(role_service: RoleService = Depends(get_role_service)):
    """List all configured roles."""
    data = await role_service.list_roles()
    return app_success(data=data)


@router.get("/{role_id}")
async def get_role_by_id(
    role_id: uuid.UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """Get single role details along with its assigned permissions."""
    data = await role_service.get_role_by_id(role_id)
    return app_success(data=data)


@router.put("/{role_id}")
async def update_role(
    role_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    role_service: RoleService = Depends(get_role_service),
):
    """Update role metadata."""
    data = await role_service.update_role(role_id=role_id, name=name, description=description)
    return app_success(
        msg="Role updated successfully",
        data=data,
    )


@router.delete("/{role_id}")
async def delete_role(
    role_id: uuid.UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """Delete a role by ID."""
    await role_service.delete_role(role_id)
    return app_success(msg="Role deleted successfully")


# ---------------------------------------------------------------------------
# Role Permission Management Endpoints
# ---------------------------------------------------------------------------
@router.get("/{role_id}/permissions")
async def get_role_permissions(
    role_id: uuid.UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """List all permissions assigned to a role."""
    data = await role_service.get_role_permissions(role_id)
    return app_success(data=data)


@router.post("/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: uuid.UUID,
    permission_ids: List[uuid.UUID],
    role_service: RoleService = Depends(get_role_service),
):
    """Replace/sync permissions for a given role with the provided list of permission IDs."""
    await role_service.sync_role_permissions(role_id, permission_ids)
    return app_success(msg="Role permissions synchronized successfully")


@router.post("/{role_id}/permissions/{permission_id}")
async def attach_permission_to_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """Attach a single permission to a role."""
    attached = await role_service.attach_permission(role_id, permission_id)
    msg = (
        "Permission attached to role successfully"
        if attached
        else "Permission is already assigned to this role"
    )
    return app_success(msg=msg)


@router.delete("/{role_id}/permissions/{permission_id}")
async def detach_permission_from_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """Detach a single permission from a role."""
    await role_service.detach_permission(role_id, permission_id)
    return app_success(msg="Permission detached from role successfully")


@router.post("/seed-defaults")
async def seed_default_roles_and_permissions(
    role_service: RoleService = Depends(get_role_service),
):
    """Seed initial permissions and standard roles (admin, doctor, nurse, cashier, patient)."""
    data = await role_service.seed_defaults()
    return app_success(
        msg="Roles (admin, doctor, nurse, cashier, patient) and permissions seeded successfully",
        data=data,
    )
