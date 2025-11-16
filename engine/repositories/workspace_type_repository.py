from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from engine.repositories.base_repository import BaseRepository
from engine.models.workspace_type_model import WorkspaceTypeModel


class WorkspaceTypeRepository(BaseRepository[WorkspaceTypeModel]):
    """
    WorkspaceTypeRepository is a repository for managing WorkspaceTypeModel objects.
    
    Attributes:
        model: WorkspaceTypeModel

    Methods:
        get_by_name(self, db_conn: AsyncSession, name: str) -> Optional[WorkspaceTypeModel]:
            Get a workspace type by name.   
    """

    def __init__(self):
        super().__init__(WorkspaceTypeModel)

    async def get_by_name(self, db_conn: AsyncSession, name: str) -> Optional[WorkspaceTypeModel]:
        query = select(self.model).where(self.model.name == name)
        result = await db_conn.execute(query)
        return result.scalar_one_or_none()
