from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Any)


class BaseRepository(Generic[ModelType]):
    """
    Generic asynchronous base repository providing standard CRUD operations
    for SQLAlchemy models.
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by its primary key ID."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by(self, **kwargs: Any) -> Optional[ModelType]:
        """Fetch the first record matching given keyword filters."""
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def filter_by(
        self,
        skip: int = 0,
        limit: int = 100,
        **kwargs: Any,
    ) -> Sequence[ModelType]:
        """Fetch records matching filters with offset and limit."""
        stmt = select(self.model).filter_by(**kwargs).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Fetch all records with offset and limit."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(self, **kwargs: Any) -> int:
        """Count records matching filters."""
        stmt = select(func.count(self.model.id)).filter_by(**kwargs)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def create(self, **kwargs: Any) -> ModelType:
        """Instantiate, add, commit, and refresh a new model instance."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def add(self, instance: ModelType) -> ModelType:
        """Add an already instantiated entity to session without committing."""
        self.db.add(instance)
        return instance

    async def update(
        self,
        db_obj: ModelType,
        obj_in: Union[BaseModel, Dict[str, Any]],
    ) -> ModelType:
        """Update an existing model instance with data from a dict or pydantic model."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> bool:
        """Delete a record by primary key."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return (result.rowcount or 0) > 0

    async def commit(self) -> None:
        """Commit the current database transaction."""
        await self.db.commit()

    async def refresh(self, db_obj: ModelType) -> None:
        """Refresh model instance with latest database state."""
        await self.db.refresh(db_obj)
