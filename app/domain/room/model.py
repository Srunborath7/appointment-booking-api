import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    room_type = Column(String(50), nullable=False, default="consultation", index=True)
    department = Column(String(100), nullable=True, index=True)
    floor = Column(String(50), nullable=True)
    building = Column(String(100), nullable=True)
    capacity = Column(Integer, default=1, nullable=False)
    status = Column(String(30), default="available", nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
