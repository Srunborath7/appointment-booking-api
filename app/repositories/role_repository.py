from typing import List, Optional
import uuid
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.auth.model import Permission, Role, RolePermission
from app.repositories.base.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Repository handling database operations for Roles, Permissions, and their associations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Role, db)

    async def get_by_name(self, name: str, load_permissions: bool = False) -> Optional[Role]:
        """Fetch role by unique role name."""
        stmt = select(Role).where(Role.name == name)
        if load_permissions:
            stmt = stmt.options(
                selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, role_id: uuid.UUID, load_permissions: bool = False) -> Optional[Role]:
        """Fetch role by UUID with optional eager loading of permissions."""
        stmt = select(Role).where(Role.id == role_id)
        if load_permissions:
            stmt = stmt.options(
                selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_roles(self, load_permissions: bool = True) -> List[Role]:
        """List all configured roles."""
        stmt = select(Role).order_by(Role.name)
        if load_permissions:
            stmt = stmt.options(
                selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # Permissions CRUD
    async def get_permission_by_id(self, perm_id: uuid.UUID) -> Optional[Permission]:
        """Fetch permission by UUID."""
        stmt = select(Permission).where(Permission.id == perm_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_permission_by_codename(self, codename: str) -> Optional[Permission]:
        """Fetch permission by codename identifier."""
        stmt = select(Permission).where(Permission.codename == codename)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_permissions(
        self,
        group: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Permission]:
        """List all available system permissions with optional group and search filtering."""
        stmt = select(Permission)
        if group:
            stmt = stmt.where(Permission.group == group)
        if search:
            search_filter = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Permission.name.ilike(search_filter),
                    Permission.codename.ilike(search_filter),
                )
            )
        stmt = stmt.order_by(Permission.group, Permission.codename)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_permission(self, codename: str, name: str, group: str) -> Permission:
        """Create and commit a new permission."""
        perm = Permission(codename=codename, name=name, group=group)
        self.db.add(perm)
        await self.db.commit()
        await self.db.refresh(perm)
        return perm

    async def delete_permission(self, permission_id: uuid.UUID) -> bool:
        """Delete a permission by ID."""
        stmt = delete(Permission).where(Permission.id == permission_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return (result.rowcount or 0) > 0

    async def get_role_permissions(self, role_id: uuid.UUID) -> List[Permission]:
        """Fetch all permissions assigned to a given role."""
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
            .order_by(Permission.group, Permission.codename)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def assign_permissions(self, role_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> None:
        """Assign permissions to a role, ignoring existing assignments."""
        for perm_id in permission_ids:
            chk = select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == perm_id,
            )
            exists = (await self.db.execute(chk)).scalar_one_or_none()
            if not exists:
                self.db.add(RolePermission(role_id=role_id, permission_id=perm_id))
        await self.db.commit()

    async def sync_role_permissions(self, role_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> None:
        """Synchronize role permissions with given list of permission IDs."""
        rp_stmt = select(RolePermission).where(RolePermission.role_id == role_id)
        existing_rps = (await self.db.execute(rp_stmt)).scalars().all()
        existing_map = {rp.permission_id: rp for rp in existing_rps}

        # Remove unselected
        for p_id, rp in existing_map.items():
            if p_id not in permission_ids:
                await self.db.delete(rp)

        # Add newly selected
        for p_id in permission_ids:
            if p_id not in existing_map:
                p_check = select(Permission).where(Permission.id == p_id)
                if (await self.db.execute(p_check)).scalar_one_or_none():
                    self.db.add(RolePermission(role_id=role_id, permission_id=p_id))

        await self.db.commit()

    async def attach_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> bool:
        """Attach single permission to a role. Returns True if attached, False if already present."""
        chk = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        exists = (await self.db.execute(chk)).scalar_one_or_none()
        if exists:
            return False

        self.db.add(RolePermission(role_id=role_id, permission_id=permission_id))
        await self.db.commit()
        return True

    async def detach_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> bool:
        """Detach single permission from role. Returns True if removed, False if not found."""
        chk = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        rp = (await self.db.execute(chk)).scalar_one_or_none()
        if not rp:
            return False

        await self.db.delete(rp)
        await self.db.commit()
        return True
