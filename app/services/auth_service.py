from typing import Any, Dict
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from app.domain.auth.model import Role, User
from app.domain.auth.schema import UserCreate, UserLogin, UserResponse
from app.repositories.auth_repository import AuthRepository
from app.repositories.role_repository import RoleRepository
from app.services.base.base_service import BaseService


class AuthService(BaseService[AuthRepository]):
    """Service handling user registration, authentication, token refresh, and identity operations."""

    def __init__(
        self,
        auth_repo: AuthRepository,
        role_repo: RoleRepository,
        db: AsyncSession,
    ):
        super().__init__(repository=auth_repo, db=db)
        self.auth_repo = auth_repo
        self.role_repo = role_repo

    async def register(self, payload: UserCreate) -> Dict[str, Any]:
        """Register a new user account and return JWT credentials."""
        # 1. Check if email already registered
        existing_user = await self.auth_repo.get_by_email(payload.email)
        if existing_user:
            raise ConflictError(f"Email '{payload.email}' is already registered")

        # 2. Resolve Role
        role_id = payload.role_id
        if role_id:
            role = await self.role_repo.get_by_id(role_id)
            if not role:
                raise NotFoundError("Specified role does not exist")
        else:
            # Default to patient, or customer/student/user
            for default_name in ["patient", "customer", "student", "user"]:
                role = await self.role_repo.get_by_name(default_name)
                if role:
                    role_id = role.id
                    break

        # 3. Create user instance
        user = await self.auth_repo.create(
            email=payload.email,
            full_name=payload.full_name,
            phone_number=payload.phone_number,
            hashed_password=hash_password(payload.password),
            role_id=role_id,
            status=payload.status.value,
            surface=payload.surface.value,
            is_verified=True,
        )

        # 4. Reload user with role populated
        user_with_role = await self.auth_repo.get_by_id(user.id, load_role=True)
        if not user_with_role:
            user_with_role = user

        # 5. Generate JWT tokens
        token_data = {
            "sub": str(user_with_role.id),
            "email": user_with_role.email,
            "role": user_with_role.role.name if user_with_role.role else None,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        user_data = UserResponse.model_validate(user_with_role).model_dump(mode="json")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data,
        }

    async def login(self, payload: UserLogin) -> Dict[str, Any]:
        """Authenticate user credentials and issue active JWT tokens."""
        user = await self.auth_repo.get_by_email(payload.email, load_role=True)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if user.status != "active":
            raise AuthenticationError("Account is inactive or suspended")

        # Update last login
        await self.auth_repo.update_last_login(user)

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.name if user.role else None,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        user_data = UserResponse.model_validate(user).model_dump(mode="json")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data,
        }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Validate refresh token and issue a fresh access token."""
        try:
            payload = verify_refresh_token(refresh_token)
        except JWTError as e:
            raise AuthenticationError(f"Invalid refresh token: {str(e)}")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Token missing user subject")

        try:
            user_uuid = uuid.UUID(str(user_id_str))
        except ValueError:
            raise AuthenticationError("Malformed user identifier in token")

        user = await self.auth_repo.get_by_id(user_uuid, load_role=True)
        if not user or user.status != "active":
            raise AuthenticationError("User is no longer active")

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.name if user.role else None,
        }
        new_access_token = create_access_token(token_data)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    async def get_my_profile(self, user: User) -> Dict[str, Any]:
        """Return profile information for current user."""
        return UserResponse.model_validate(user).model_dump(mode="json")
