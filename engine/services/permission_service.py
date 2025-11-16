from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.permission_model import PermissionModel
from engine.repositories.permission_repository import PermissionRepository
from engine.services.base_service import BaseService


class PermissionService(BaseService[PermissionModel]):
    def __init__(self):
        repository = PermissionRepository()
        super().__init__(repository)
        self.repository = repository

    async def get_all_groups(self, db_conn: AsyncSession) -> List[str]:
        """
        Get all unique group names from permissions.
        
        Returns:
            List[str]: List of unique group names, excluding None values and deleted permissions
        """
        query = (
            select(PermissionModel.group)
            .distinct()
            .where(PermissionModel.group.isnot(None))
            .where(PermissionModel.is_deleted == False)
            .order_by(PermissionModel.group)
        )
        result = await db_conn.execute(query)
        # Explicitly convert each value to string to ensure proper serialization
        groups = result.scalars().all()
        return [str(group) for group in groups if group is not None]
