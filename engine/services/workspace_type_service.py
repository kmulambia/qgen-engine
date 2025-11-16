from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.workspace_type_model import WorkspaceTypeModel
from engine.repositories.workspace_type_repository import WorkspaceTypeRepository
from engine.services.base_service import BaseService


class WorkspaceTypeService(BaseService[WorkspaceTypeModel]):
    """
    WorkspaceTypeService is a service for managing workspace types.
    
    Attributes:
        repository: WorkspaceTypeRepository

    Methods:
        get_by_name(self, name: str) -> Optional[WorkspaceTypeModel]:
            Get a workspace type by name.
    """

    def __init__(self):
        self.repository: WorkspaceTypeRepository = WorkspaceTypeRepository()
        super().__init__(self.repository)

    async def get_by_name(self, db_conn: AsyncSession, name: str) -> Optional[WorkspaceTypeModel]:
        return await self.repository.get_by_name(db_conn, name)
