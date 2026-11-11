from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.model import Permission, Role, RolePermission


# Structured definitions for system auth & role permissions
PERMISSION_DEFINITIONS = [
    {
        "group": "Dashboard",
        "permissions": [
            ("View dashboard", "dashboard.view"),
        ],
    },
    {
        "group": "User Management",
        "permissions": [
            ("View users", "user.view"),
            ("Create new user", "user.create"),
            ("Edit user details", "user.edit"),
            ("Delete user", "user.delete"),
            ("Change user status", "user.status.update"),
        ],
    },
    {
        "group": "Role & Permissions",
        "permissions": [
            ("View roles", "role.view"),
            ("Create new role", "role.create"),
            ("Edit role", "role.edit"),
            ("Delete role", "role.delete"),
            ("Assign permissions to role", "role.assign_permissions"),
        ],
    },
    {
        "group": "System Settings",
        "permissions": [
            ("View system settings", "settings.view"),
            ("Update system settings", "settings.edit"),
        ],
    },
]


def get_flat_permissions() -> List[Dict[str, str]]:
    """Return all permissions as a flattened list of dicts."""
    flat = []
    for group in PERMISSION_DEFINITIONS:
        for name, codename in group["permissions"]:
            flat.append({"group": group["group"], "name": name, "codename": codename})
    return flat


def get_all_codenames() -> List[str]:
    """Return all permission codenames."""
    return [p["codename"] for p in get_flat_permissions()]


async def seed_permissions(db: AsyncSession) -> None:
    """Seed default permissions into the database if not present."""
    for item in get_flat_permissions():
        stmt = select(Permission).where(Permission.codename == item["codename"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            perm = Permission(
                codename=item["codename"],
                name=item["name"],
                group=item["group"],
            )
            db.add(perm)
    await db.commit()


async def assign_all_permissions_to_role(db: AsyncSession, role_name: str) -> None:
    """Assign all available permissions to a given role (e.g. super_admin or admin)."""
    stmt = select(Role).where(Role.name == role_name)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        return

    # Fetch all permissions
    perms_stmt = select(Permission)
    perms_res = await db.execute(perms_stmt)
    all_perms = perms_res.scalars().all()

    # Fetch existing role permissions
    rp_stmt = select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
    rp_res = await db.execute(rp_stmt)
    existing_perm_ids = set(rp_res.scalars().all())

    for perm in all_perms:
        if perm.id not in existing_perm_ids:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    await db.commit()


class PermissionChecker:
    """Dependency that checks if the authenticated user has the required permission."""

    def __init__(self, required_permission: str) -> None:
        self.required_permission = required_permission

    async def __call__(self, current_user: Any, db: AsyncSession) -> bool:
        from app.core.exceptions import AuthorizationError

        if not current_user:
            raise AuthorizationError("Authentication required")

        # Super admin has unrestricted access
        if getattr(current_user.role, "name", None) == "super_admin":
            return True

        # Check user's role permissions
        if not current_user.role_id:
            raise AuthorizationError("User has no role assigned")

        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == current_user.role_id,
                Permission.codename == self.required_permission,
            )
        )
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()
        if not perm:
            raise AuthorizationError(f"Permission denied: '{self.required_permission}' required")
        return True
