from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import RoleName
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import (
    PERMISSION_DEFINITIONS,
    ROLE_PERMISSIONS_MAPPING,
    assign_all_permissions_to_role,
    assign_permissions_to_role_by_codenames,
    seed_permissions,
)
from app.domain.auth.model import Role
from app.domain.auth.schema import (
    PermissionCreate,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
)
from app.repositories.role_repository import RoleRepository
from app.services.base.base_service import BaseService


class RoleService(BaseService[RoleRepository]):
    """Service handling role configurations, permission associations, and security roles."""

    def __init__(self, role_repo: RoleRepository, db: AsyncSession):
        super().__init__(repository=role_repo, db=db)
        self.role_repo = role_repo

    async def create_role(self, payload: RoleCreate) -> Dict[str, Any]:
        """Create a new role with optional initial permissions."""
        existing = await self.role_repo.get_by_name(payload.name)
        if existing:
            raise ConflictError(f"Role '{payload.name}' already exists")

        role = await self.role_repo.create(
            name=payload.name,
            description=payload.description,
        )

        if payload.permission_ids:
            valid_ids = []
            for p_id in payload.permission_ids:
                p = await self.role_repo.get_permission_by_id(p_id)
                if p:
                    valid_ids.append(p.id)
            if valid_ids:
                await self.role_repo.assign_permissions(role.id, valid_ids)

        return RoleResponse.model_validate(role).model_dump(mode="json")

    async def list_roles(self) -> List[Dict[str, Any]]:
        """List all roles along with their assigned permissions."""
        roles = await self.role_repo.list_roles(load_permissions=True)
        results = []
        for r in roles:
            role_dict = RoleResponse.model_validate(r).model_dump(mode="json")
            role_dict["permissions"] = [
                PermissionResponse.model_validate(rp.permission).model_dump(mode="json")
                for rp in r.role_permissions
                if rp.permission
            ]
            results.append(role_dict)
        return results

    async def get_role_by_id(self, role_id: uuid.UUID) -> Dict[str, Any]:
        """Fetch role details with permissions."""
        role = await self.role_repo.get_by_id(role_id, load_permissions=True)
        if not role:
            raise NotFoundError(f"Role with id '{role_id}' not found")

        role_dict = RoleResponse.model_validate(role).model_dump(mode="json")
        role_dict["permissions"] = [
            PermissionResponse.model_validate(rp.permission).model_dump(mode="json")
            for rp in role.role_permissions
            if rp.permission
        ]
        return role_dict

    async def update_role(
        self,
        role_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update role metadata."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with id '{role_id}' not found")

        if name and name != role.name:
            dup = await self.role_repo.get_by_name(name)
            if dup:
                raise ConflictError(f"Role name '{name}' already exists")
            role.name = name

        if description is not None:
            role.description = description

        await self.role_repo.commit()
        await self.role_repo.refresh(role)
        return RoleResponse.model_validate(role).model_dump(mode="json")

    async def delete_role(self, role_id: uuid.UUID) -> bool:
        """Delete a role by ID."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with id '{role_id}' not found")
        return await self.role_repo.delete(role_id)

    async def get_role_permissions(self, role_id: uuid.UUID) -> List[Dict[str, Any]]:
        """List all permissions assigned to a role."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with id '{role_id}' not found")

        perms = await self.role_repo.get_role_permissions(role_id)
        return [PermissionResponse.model_validate(p).model_dump(mode="json") for p in perms]

    async def sync_role_permissions(
        self, role_id: uuid.UUID, permission_ids: List[uuid.UUID]
    ) -> None:
        """Replace all assigned permissions for a given role with specified permission IDs."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with id '{role_id}' not found")

        await self.role_repo.sync_role_permissions(role_id, permission_ids)

    async def attach_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> bool:
        """Attach a single permission to a role."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with id '{role_id}' not found")

        perm = await self.role_repo.get_permission_by_id(permission_id)
        if not perm:
            raise NotFoundError(f"Permission with id '{permission_id}' not found")

        return await self.role_repo.attach_permission(role_id, permission_id)

    async def detach_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        """Detach a single permission from a role."""
        removed = await self.role_repo.detach_permission(role_id, permission_id)
        if not removed:
            raise NotFoundError("Permission assignment not found for this role")

    # Permissions management
    async def create_permission(self, payload: PermissionCreate) -> Dict[str, Any]:
        """Create a new permission definition."""
        existing = await self.role_repo.get_permission_by_codename(payload.codename)
        if existing:
            raise ConflictError(f"Permission with codename '{payload.codename}' already exists")

        perm = await self.role_repo.create_permission(
            codename=payload.codename,
            name=payload.name,
            group=payload.group,
        )
        return PermissionResponse.model_validate(perm).model_dump(mode="json")

    async def list_permissions(
        self,
        group: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all system permissions with definitions catalog."""
        permissions = await self.role_repo.list_permissions(group=group, search=search)
        perms_data = [PermissionResponse.model_validate(p).model_dump(mode="json") for p in permissions]
        return {
            "definitions": PERMISSION_DEFINITIONS,
            "permissions": perms_data,
        }

    async def get_permission_by_id(self, permission_id: uuid.UUID) -> Dict[str, Any]:
        """Fetch permission by ID."""
        perm = await self.role_repo.get_permission_by_id(permission_id)
        if not perm:
            raise NotFoundError(f"Permission with id '{permission_id}' not found")
        return PermissionResponse.model_validate(perm).model_dump(mode="json")

    async def delete_permission(self, permission_id: uuid.UUID) -> bool:
        """Delete permission definition."""
        perm = await self.role_repo.get_permission_by_id(permission_id)
        if not perm:
            raise NotFoundError(f"Permission with id '{permission_id}' not found")
        return await self.role_repo.delete_permission(permission_id)

    async def seed_system_permissions(self) -> None:
        """Seed system permissions catalog."""
        await seed_permissions(self.db)

    async def seed_defaults(self) -> Dict[str, Any]:
        """Seed initial permissions and standard roles with assigned permissions."""
        await seed_permissions(self.db)

        default_roles = [
            (RoleName.ADMIN.value, "Platform and clinic administrator with full access"),
            (RoleName.DOCTOR.value, "Medical Doctor - consultations and appointments"),
            (RoleName.NURSE.value, "Nurse - patient care, triage, and scheduling"),
            (RoleName.CASHIER.value, "Cashier - billing, invoicing, and payments"),
            (RoleName.PATIENT.value, "Patient / Client booking appointments"),
        ]

        created = []
        for r_name, r_desc in default_roles:
            role = await self.role_repo.get_by_name(r_name)
            if not role:
                await self.role_repo.create(name=r_name, description=r_desc)
                created.append(r_name)

        # Assign permissions according to mapping
        for role_name, mapping in ROLE_PERMISSIONS_MAPPING.items():
            if mapping == "ALL":
                await assign_all_permissions_to_role(self.db, role_name)
            else:
                await assign_permissions_to_role_by_codenames(self.db, role_name, mapping)

        return {"created_roles": created}
