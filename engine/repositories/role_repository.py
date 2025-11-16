from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from engine.models import RoleModel
from engine.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[RoleModel]):
    """
    RoleRepository class for managing RoleModel objects.
    
    Attributes:

    Methods:
        get_by_name(self, name: str) -> Optional[RoleModel]:
            Get a role by name.
    """
    def __init__(self):
        super().__init__(RoleModel)

    async def get_by_name(self, db_conn: AsyncSession, name: str) -> Optional[RoleModel]:
        query = select(self.model).where(self.model.name == name)
        result = await db_conn.execute(query)
        return result.scalar_one_or_none()
