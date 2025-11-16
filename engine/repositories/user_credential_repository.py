from engine.models import UserCredentialModel
from engine.repositories.base_repository import BaseRepository
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID


class UserCredentialRepository(BaseRepository[UserCredentialModel]):
    """
    UserCredentialRepository is a repository that handles user credentials.

    Attributes:

    Methods:
        get_latest_user_credential: Get the latest active user credential.
        deactivate_all_user_credentials: Deactivate all user credentials.
    """

    def __init__(self):
        super().__init__(UserCredentialModel)

    @staticmethod
    async def get_latest_user_credential(db_conn: AsyncSession, user_id: UUID):
        query = select(UserCredentialModel).where(
            and_(
                UserCredentialModel.user_id == user_id,
                UserCredentialModel.status == "active",
                UserCredentialModel.is_deleted.is_(False)
            )
        ).order_by(UserCredentialModel.created_at.desc()).limit(1)
        result = await db_conn.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def deactivate_all_user_credentials(db_conn: AsyncSession, user_id: UUID):
        await db_conn.execute(
            update(UserCredentialModel)
            .where(UserCredentialModel.user_id == user_id)
            .values(status="inactive")
        )
