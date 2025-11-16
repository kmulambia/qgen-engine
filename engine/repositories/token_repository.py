from sqlalchemy import select
from engine.models import TokenModel
from engine.repositories.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from typing import Optional
from uuid import UUID


class TokenRepository(BaseRepository[TokenModel]):
    """
    TokenRepository is a repository for managing tokens.

    Attributes:
        model: TokenModel

    Methods:
        get_latest_token: Get the latest token for a user.
    """

    def __init__(self):
        super().__init__(TokenModel)

    @staticmethod
    async def get_latest_token(db_conn: AsyncSession, user_id: UUID) -> Optional[TokenModel]:
        query = select(TokenModel).where(
            and_(
                TokenModel.user_id == user_id,
                TokenModel.status == "active"
            )
        )
        result = await db_conn.execute(query)
        return result.scalar_one_or_none()
