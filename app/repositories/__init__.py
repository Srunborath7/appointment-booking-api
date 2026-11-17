from app.repositories.base.base_repository import BaseRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.room_repository import RoomRepository

__all__ = [
    "BaseRepository",
    "AuthRepository",
    "RoleRepository",
    "PatientRepository",
    "RoomRepository",
]
