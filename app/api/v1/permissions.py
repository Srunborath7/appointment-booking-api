import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import PERMISSION_DEFINITIONS, seed_permissions
from app.core.responses import app_success
from app.domain.auth import Permission, PermissionCreate, PermissionResponse

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_permission(payload: PermissionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new permission definition."""
    # Check if codename already exists
    existing_stmt = select(Permission).where(Permission.codename == payload.codename)
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise ConflictError(f"Permission with codename '{payload.codename}' already exists")

    new_perm = Permission(
        codename=payload.codename,
        name=payload.name,
        group=payload.group,
    )
    db.add(new_perm)
    await db.commit()
    await db.refresh(new_perm)

    return app_success(
        msg="Permission created successfully",
        code=status.HTTP_201_CREATED,
        data=PermissionResponse.model_validate(new_perm).model_dump(mode="json"),
    )


@router.get("")
async def list_permissions(
    group: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all available permissions with optional group and search filters."""
    stmt = select(Permission)
    if group:
        stmt = stmt.where(Permission.group == group)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            (Permission.name.ilike(search_filter)) | (Permission.codename.ilike(search_filter))
        )

    stmt = stmt.order_by(Permission.group, Permission.codename)
    res = await db.execute(stmt)
    perms = res.scalars().all()
    data = [PermissionResponse.model_validate(p).model_dump(mode="json") for p in perms]
    return app_success(data={"definitions": PERMISSION_DEFINITIONS, "permissions": data})


@router.get("/{permission_id}")
async def get_permission_by_id(permission_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get single permission details."""
    stmt = select(Permission).where(Permission.id == permission_id)
    res = await db.execute(stmt)
    perm = res.scalar_one_or_none()
    if not perm:
        raise NotFoundError(f"Permission with id '{permission_id}' not found")
    return app_success(data=PermissionResponse.model_validate(perm).model_dump(mode="json"))


@router.delete("/{permission_id}")
async def delete_permission(permission_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a permission by ID."""
    stmt = select(Permission).where(Permission.id == permission_id)
    res = await db.execute(stmt)
    perm = res.scalar_one_or_none()
    if not perm:
        raise NotFoundError(f"Permission with id '{permission_id}' not found")

    await db.delete(perm)
    await db.commit()
    return app_success(msg="Permission deleted successfully")


@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_system_permissions(db: AsyncSession = Depends(get_db)):
    """Seed initial system permission catalog."""
    await seed_permissions(db)
    return app_success(msg="System permissions seeded successfully")
