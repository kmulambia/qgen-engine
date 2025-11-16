from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.role_model import RoleModel
from engine.repositories.role_repository import RoleRepository
from engine.services.base_service import BaseService


class RoleService(BaseService[RoleModel]):
    """
    RoleService is a service for managing roles.

    Attributes:
        repository: RoleRepository

    Methods:
        get_by_name(self, db_conn: AsyncSession, name: str) -> Optional[RoleModel]:
            Get a role by name.
    """

    def __init__(self):
        self.repository: RoleRepository = RoleRepository()
        super().__init__(self.repository)

    async def get_by_name(self, db_conn: AsyncSession, name: str) -> Optional[RoleModel]:
        return await self.repository.get_by_name(db_conn, name)
