from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.domain.auth.model import User
from app.domain.auth.schema import UserCreate, UserResponse, UserUpdate
from app.repositories.auth_repository import AuthRepository
from app.repositories.role_repository import RoleRepository
from app.services.base.base_service import BaseService


class UserService(BaseService[AuthRepository]):
    """Service handling administrative and user account management operations."""

    def __init__(
        self,
        auth_repo: AuthRepository,
        role_repo: RoleRepository,
        db: AsyncSession,
    ):
        super().__init__(repository=auth_repo, db=db)
        self.auth_repo = auth_repo
        self.role_repo = role_repo

    async def create_user(self, payload: UserCreate) -> Dict[str, Any]:
        """Create a new user with optional role assignment."""
        existing = await self.auth_repo.get_by_email(payload.email)
        if existing:
            raise ConflictError(f"Email '{payload.email}' is already registered")

        if payload.role_id:
            role = await self.role_repo.get_by_id(payload.role_id)
            if not role:
                raise NotFoundError(f"Role with id '{payload.role_id}' not found")

        user = await self.auth_repo.create(
            email=payload.email,
            full_name=payload.full_name,
            phone_number=payload.phone_number,
            hashed_password=hash_password(payload.password),
            role_id=payload.role_id,
            status=payload.status.value,
            surface=payload.surface.value,
            is_verified=True,
        )

        user_with_role = await self.auth_repo.get_by_id(user.id, load_role=True)
        return UserResponse.model_validate(user_with_role or user).model_dump(mode="json")

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """List users with pagination, returning (items, total_records, total_pages)."""
        users, total_records = await self.auth_repo.list_users(
            page=page,
            page_size=page_size,
            role_id=role_id,
            status_filter=status_filter,
            search=search,
        )

        total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 0
        data = [UserResponse.model_validate(u).model_dump(mode="json") for u in users]
        return data, total_records, total_pages

    async def get_user_by_id(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Fetch user by ID."""
        user = await self.auth_repo.get_by_id(user_id, load_role=True)
        if not user:
            raise NotFoundError(f"User with id '{user_id}' not found")
        return UserResponse.model_validate(user).model_dump(mode="json")

    async def update_user(self, user_id: uuid.UUID, payload: UserUpdate) -> Dict[str, Any]:
        """Update user properties."""
        user = await self.auth_repo.get_by_id(user_id, load_role=True)
        if not user:
            raise NotFoundError(f"User with id '{user_id}' not found")

        update_dict = payload.model_dump(exclude_unset=True)

        if "role_id" in update_dict and update_dict["role_id"]:
            role = await self.role_repo.get_by_id(update_dict["role_id"])
            if not role:
                raise NotFoundError(f"Role with id '{update_dict['role_id']}' not found")

        if "password" in update_dict and update_dict["password"]:
            update_dict["hashed_password"] = hash_password(update_dict.pop("password"))

        if "status" in update_dict and update_dict["status"]:
            update_dict["status"] = update_dict["status"].value

        updated_user = await self.auth_repo.update(user, update_dict)
        refreshed = await self.auth_repo.get_by_id(updated_user.id, load_role=True)
        return UserResponse.model_validate(refreshed or updated_user).model_dump(mode="json")

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete user account."""
        user = await self.auth_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with id '{user_id}' not found")
        return await self.auth_repo.delete(user_id)
