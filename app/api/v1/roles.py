import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.enum import RoleName
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import assign_all_permissions_to_role, seed_permissions
from app.core.responses import app_success
from app.domain.auth import (
    Permission,
    PermissionResponse,
    Role,
    RoleCreate,
    RolePermission,
    RoleResponse,
)

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(payload: RoleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new role with optional permission assignments."""
    existing_stmt = select(Role).where(Role.name == payload.name)
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise ConflictError(f"Role '{payload.name}' already exists")

    new_role = Role(name=payload.name, description=payload.description)
    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)

    # Assign initial permissions if supplied
    if payload.permission_ids:
        for perm_id in payload.permission_ids:
            # Check permission exists
            p_stmt = select(Permission).where(Permission.id == perm_id)
            if (await db.execute(p_stmt)).scalar_one_or_none():
                db.add(RolePermission(role_id=new_role.id, permission_id=perm_id))
        await db.commit()

    return app_success(
        msg="Role created successfully",
        code=status.HTTP_201_CREATED,
        data=RoleResponse.model_validate(new_role).model_dump(mode="json"),
    )


@router.get("")
async def list_roles(db: AsyncSession = Depends(get_db)):
    """List all configured roles."""
    stmt = (
        select(Role)
        .options(
            selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
        .order_by(Role.name)
    )
    res = await db.execute(stmt)
    roles = res.scalars().all()

    data = []
    for r in roles:
        role_dict = RoleResponse.model_validate(r).model_dump(mode="json")
        role_dict["permissions"] = [
            PermissionResponse.model_validate(rp.permission).model_dump(mode="json")
            for rp in r.role_permissions
            if rp.permission
        ]
        data.append(role_dict)

    return app_success(data=data)


@router.get("/{role_id}")
async def get_role_by_id(role_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get single role details along with its assigned permissions."""
    stmt = (
        select(Role)
        .options(
            selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
        .where(Role.id == role_id)
    )
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise NotFoundError(f"Role with id '{role_id}' not found")

    role_dict = RoleResponse.model_validate(role).model_dump(mode="json")
    role_dict["permissions"] = [
        PermissionResponse.model_validate(rp.permission).model_dump(mode="json")
        for rp in role.role_permissions
        if rp.permission
    ]
    return app_success(data=role_dict)


@router.put("/{role_id}")
async def update_role(
    role_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update role metadata."""
    stmt = select(Role).where(Role.id == role_id)
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise NotFoundError(f"Role with id '{role_id}' not found")

    if name:
        # Check uniqueness if name changed
        if name != role.name:
            dup_stmt = select(Role).where(Role.name == name)
            if (await db.execute(dup_stmt)).scalar_one_or_none():
                raise ConflictError(f"Role name '{name}' already exists")
        role.name = name

    if description is not None:
        role.description = description

    await db.commit()
    await db.refresh(role)
    return app_success(
        msg="Role updated successfully",
        data=RoleResponse.model_validate(role).model_dump(mode="json"),
    )


@router.delete("/{role_id}")
async def delete_role(role_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a role by ID."""
    stmt = select(Role).where(Role.id == role_id)
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        raise NotFoundError(f"Role with id '{role_id}' not found")

    await db.delete(role)
    await db.commit()
    return app_success(msg="Role deleted successfully")


# ---------------------------------------------------------------------------
# Role Permission Management Endpoints
# ---------------------------------------------------------------------------
@router.get("/{role_id}/permissions")
async def get_role_permissions(role_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all permissions assigned to a role."""
    stmt = (
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
        .order_by(Permission.group, Permission.codename)
    )
    res = await db.execute(stmt)
    perms = res.scalars().all()
    data = [PermissionResponse.model_validate(p).model_dump(mode="json") for p in perms]
    return app_success(data=data)


@router.post("/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: uuid.UUID,
    permission_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
):
    """Replace/sync permissions for a given role with the provided list of permission IDs."""
    role_stmt = select(Role).where(Role.id == role_id)
    role_res = await db.execute(role_stmt)
    if not role_res.scalar_one_or_none():
        raise NotFoundError(f"Role with id '{role_id}' not found")

    # Fetch existing role permissions
    rp_stmt = select(RolePermission).where(RolePermission.role_id == role_id)
    existing_rps = (await db.execute(rp_stmt)).scalars().all()
    existing_map = {rp.permission_id: rp for rp in existing_rps}

    # Delete unselected
    for perm_id, rp_obj in existing_map.items():
        if perm_id not in permission_ids:
            await db.delete(rp_obj)

    # Add newly selected
    for perm_id in permission_ids:
        if perm_id not in existing_map:
            # Verify permission exists
            p_check = select(Permission).where(Permission.id == perm_id)
            if (await db.execute(p_check)).scalar_one_or_none():
                db.add(RolePermission(role_id=role_id, permission_id=perm_id))

    await db.commit()
    return app_success(msg="Role permissions synchronized successfully")


@router.post("/{role_id}/permissions/{permission_id}")
async def attach_permission_to_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Attach a single permission to a role."""
    # Verify role
    role_stmt = select(Role).where(Role.id == role_id)
    if not (await db.execute(role_stmt)).scalar_one_or_none():
        raise NotFoundError("Role not found")

    # Verify permission
    perm_stmt = select(Permission).where(Permission.id == permission_id)
    if not (await db.execute(perm_stmt)).scalar_one_or_none():
        raise NotFoundError("Permission not found")

    # Check if already attached
    rp_stmt = select(RolePermission).where(
        RolePermission.role_id == role_id, RolePermission.permission_id == permission_id
    )
    if (await db.execute(rp_stmt)).scalar_one_or_none():
        return app_success(msg="Permission is already assigned to this role")

    db.add(RolePermission(role_id=role_id, permission_id=permission_id))
    await db.commit()
    return app_success(msg="Permission attached to role successfully")


@router.delete("/{role_id}/permissions/{permission_id}")
async def detach_permission_from_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Detach a single permission from a role."""
    rp_stmt = select(RolePermission).where(
        RolePermission.role_id == role_id, RolePermission.permission_id == permission_id
    )
    res = await db.execute(rp_stmt)
    rp = res.scalar_one_or_none()
    if not rp:
        raise NotFoundError("Permission assignment not found for this role")

    await db.delete(rp)
    await db.commit()
    return app_success(msg="Permission detached from role successfully")


@router.post("/seed-defaults")
async def seed_default_roles_and_permissions(db: AsyncSession = Depends(get_db)):
    """Seed initial permissions and standard roles (super_admin, admin, staff, teacher, student)."""
    await seed_permissions(db)

    default_roles = [
        (RoleName.SUPER_ADMIN.value, "Super administrator with full access"),
        (RoleName.ADMIN.value, "Platform administrator"),
        (RoleName.STAFF.value, "Staff member"),
        (RoleName.TEACHER.value, "Teacher / Service Provider"),
        (RoleName.STUDENT.value, "Student / Client"),
    ]

    created = []
    for r_name, r_desc in default_roles:
        stmt = select(Role).where(Role.name == r_name)
        role = (await db.execute(stmt)).scalar_one_or_none()
        if not role:
            role = Role(name=r_name, description=r_desc)
            db.add(role)
            await db.commit()
            await db.refresh(role)
            created.append(r_name)

    await assign_all_permissions_to_role(db, RoleName.SUPER_ADMIN.value)
    await assign_all_permissions_to_role(db, RoleName.ADMIN.value)

    return app_success(
        msg="Default roles and permissions seeded successfully",
        data={"created_roles": created},
    )
