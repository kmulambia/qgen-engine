from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.user_workspace_model import UserWorkspaceModel
from engine.repositories.user_workspace_repository import UserWorkspaceRepository
from engine.services.base_service import BaseService


class UserWorkspaceService(BaseService[UserWorkspaceModel]):
    """
    UserWorkspaceService is a service for managing user workspaces.
    
    Attributes:
        repository: UserWorkspaceRepository

    Methods:
        get_default_user_workspace(self, user_id: UUID) -> Optional[UserWorkspaceModel]:
            Get the default user workspace for a user.
        get_user_workspaces(self, user_id: UUID) -> List[UserWorkspaceModel]:
            Get all user workspaces for a user.
    """

    def __init__(self):
        self.repository: UserWorkspaceRepository = UserWorkspaceRepository()
        super().__init__(self.repository)

    # TODO : Check Implementation of this function
    async def get_user_workspace_by_id(self, db_conn: AsyncSession, workspace_id: UUID,
                                       user_id: Optional[UUID] = None) -> Optional[UserWorkspaceModel]:  # Noqa
        return await self.repository.get_user_workspace_by_id(db_conn, workspace_id)

    async def get_default_user_workspace(self, db_conn: AsyncSession, user_id: UUID) -> Optional[UserWorkspaceModel]:
        return await self.repository.get_default_user_workspace(db_conn, user_id)

    async def get_user_workspaces(self, db_conn: AsyncSession, user_id: UUID) -> List[UserWorkspaceModel]:
        return await self.repository.get_user_workspaces(db_conn, user_id)
