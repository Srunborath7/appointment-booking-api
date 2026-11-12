from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories import AuthRepository, PatientRepository, RoleRepository
from app.services.auth_service import AuthService
from app.services.base.base_service import BaseService
from app.services.patient_service import PatientService
from app.services.role_service import RoleService
from app.services.user_service import UserService


# Repository Providers
def get_auth_repository(db: AsyncSession = Depends(get_db)) -> AuthRepository:
    return AuthRepository(db)


def get_role_repository(db: AsyncSession = Depends(get_db)) -> RoleRepository:
    return RoleRepository(db)


def get_patient_repository(db: AsyncSession = Depends(get_db)) -> PatientRepository:
    return PatientRepository(db)


# Service Providers
def get_auth_service(
    auth_repo: AuthRepository = Depends(get_auth_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    return AuthService(auth_repo=auth_repo, role_repo=role_repo, db=db)


def get_user_service(
    auth_repo: AuthRepository = Depends(get_auth_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
    db: AsyncSession = Depends(get_db),
) -> UserService:
    return UserService(auth_repo=auth_repo, role_repo=role_repo, db=db)


def get_role_service(
    role_repo: RoleRepository = Depends(get_role_repository),
    db: AsyncSession = Depends(get_db),
) -> RoleService:
    return RoleService(role_repo=role_repo, db=db)


def get_patient_service(
    patient_repo: PatientRepository = Depends(get_patient_repository),
    auth_repo: AuthRepository = Depends(get_auth_repository),
    db: AsyncSession = Depends(get_db),
) -> PatientService:
    return PatientService(patient_repo=patient_repo, auth_repo=auth_repo, db=db)


__all__ = [
    "BaseService",
    "AuthService",
    "UserService",
    "RoleService",
    "PatientService",
    "get_auth_repository",
    "get_role_repository",
    "get_patient_repository",
    "get_auth_service",
    "get_user_service",
    "get_role_service",
    "get_patient_service",
]
