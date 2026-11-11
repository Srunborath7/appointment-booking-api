import secrets
from typing import Callable, Optional
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.lib.translate import get_translation
from app.core.security import JWTError, verify_access_token
from app.domain.auth.model import User

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer JWT token and return current User entity from database."""
    token = credentials.credentials
    try:
        payload = verify_access_token(token)
    except JWTError as e:
        raise AuthenticationError(f"Invalid authentication token: {str(e)}")

    user_id_str = payload.get("sub") or payload.get("user_id") or payload.get("id")
    if not user_id_str:
        raise AuthenticationError("Token payload missing subject identifier")

    try:
        user_uuid = UUID(str(user_id_str))
    except ValueError:
        raise AuthenticationError("Invalid user identifier in token")

    stmt = select(User).options(selectinload(User.role)).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError(get_translation("unauthorized"))

    if user.status != "active":
        raise AuthenticationError("User account is inactive or disabled")

    return user


def require_permission(codename: str) -> Callable:
    """Dependency factory returning a dependency that asserts the user has `codename` permission."""
    from app.core.permissions import PermissionChecker

    checker = PermissionChecker(codename)

    async def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        await checker(current_user, db)
        return current_user

    return permission_dependency


async def verify_internal_api_key(
    internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
) -> str:
    """Ensure service-to-service internal requests supply valid internal API key."""
    expected_key = getattr(settings, "INTERNAL_API_KEY", None)
    if not expected_key or not internal_api_key:
        raise AuthenticationError("Internal API key required")

    if not secrets.compare_digest(internal_api_key, expected_key):
        raise AuthenticationError("Invalid internal API key")

    return internal_api_key
