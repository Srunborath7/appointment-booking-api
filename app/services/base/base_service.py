import logging
from typing import Generic, Optional, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

RepoType = TypeVar("RepoType")


class BaseService(Generic[RepoType]):
    """
    Base service class encapsulates business logic workflows and transactional coordination.
    """

    def __init__(self, repository: RepoType, db: Optional[AsyncSession] = None):
        self.repository = repository
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
