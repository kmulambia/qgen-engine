from engine.models import UserWorkspaceModel
from engine.repositories.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from engine.models.workspace_model import WorkspaceModel
from typing import Optional, List
from uuid import UUID


class UserWorkspaceRepository(BaseRepository[UserWorkspaceModel]):
    """
    UserWorkspaceRepository is a repository for managing user workspaces.

    Attributes:
        model: UserWorkspaceModel

    Methods:
        get_default_user_workspace: Get the default user workspace for a user.
        get_user_workspaces: Get all user workspaces for a user.
    """

    def __init__(self):
        super().__init__(UserWorkspaceModel)

    @staticmethod
    async def get_default_user_workspace(db_conn: AsyncSession, user_id: UUID) -> Optional[UserWorkspaceModel]:
        try:
            query = (
                select(UserWorkspaceModel)
                .options(
                    joinedload(UserWorkspaceModel.workspace).joinedload(WorkspaceModel.workspace_type)
                )
                .where(
                    and_(
                        UserWorkspaceModel.user_id == user_id,
                        UserWorkspaceModel.is_deleted.is_(False),
                        UserWorkspaceModel.status == "active",
                        UserWorkspaceModel.is_default.is_(True)
                    )
                )
                .order_by(
                    UserWorkspaceModel.created_at.desc()
                )
            )
            result = await db_conn.execute(query)
            return result.scalars().first()
        finally:
            await db_conn.close()

    @staticmethod
    async def get_user_workspaces(db_conn: AsyncSession, user_id: UUID) -> List[UserWorkspaceModel]:  # noqa
        try:
            query = (
                select(UserWorkspaceModel)
                .options(
                    joinedload(UserWorkspaceModel.workspace).joinedload(WorkspaceModel.workspace_type)
                )
                .where(
                    and_(
                        UserWorkspaceModel.user_id == user_id,
                        UserWorkspaceModel.is_deleted.is_(False),
                        UserWorkspaceModel.status == "active"
                    )
                )
                .order_by(
                    UserWorkspaceModel.is_default.desc(),
                    UserWorkspaceModel.created_at.desc()
                )
            )
            result = await db_conn.execute(query)
            items = result.scalars().all()
            return items if items else []
        finally:
            await db_conn.close()

    @staticmethod
    async def get_user_workspace_by_id(db_conn: AsyncSession, user_workspace_id: UUID) -> Optional[UserWorkspaceModel]:
        try:
            query = (
                select(UserWorkspaceModel)
                .options(
                    joinedload(UserWorkspaceModel.workspace).joinedload(WorkspaceModel.workspace_type)
                )
                .where(
                    and_(
                        UserWorkspaceModel.id == user_workspace_id,
                        UserWorkspaceModel.is_deleted.is_(False),
                        UserWorkspaceModel.status == "active"
                    )
                )
            )

            result = await db_conn.execute(query)
            return result.scalars().first()

        finally:
            await db_conn.close()
