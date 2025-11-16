from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.role_permission_model import RolePermissionModel
from engine.repositories.role_permission_repository import RolePermissionRepository
from engine.services.base_service import BaseService


class RolePermissionService(BaseService[RolePermissionModel]):
    """
    RolePermissionService is a service for managing role permissions.
    
    Attributes:

    Methods:
        get_by_role_id(self, role_id: UUID) -> List[RolePermissionModel]:
            Get all role permissions for a role.
    """
    def __init__(self):
        super().__init__(RolePermissionRepository())

    async def get_by_role_id(self, db_conn: AsyncSession, role_id: UUID) -> List[RolePermissionModel]:
        query = (
            select(self.repository.model)
            .where(RolePermissionModel.role_id == role_id)
        )
        result = await db_conn.execute(query)
        return list(result.scalars().all())

   