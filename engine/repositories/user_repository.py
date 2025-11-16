from typing import Optional
from sqlalchemy import select, and_ 
from engine.models import UserModel
from engine.repositories.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[UserModel]):
    """
    UserRepository is a repository that handles user data.
    Methods:
        get_user_by_email: Get a user by email.
        get_user_by_phone: Get a user by phone.
    """

    def __init__(self):
        super().__init__(UserModel)

    @staticmethod
    async def get_user_by_email(db_conn: AsyncSession, email: str) -> Optional[UserModel]:
        query = select(UserModel).where(
            and_(
                UserModel.email == email,
                UserModel.is_deleted.is_(False)
            )
        )
        result = await db_conn.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_phone(db_conn: AsyncSession, phone: str) -> Optional[UserModel]:
        query = select(UserModel).where(
            and_(
                UserModel.phone == phone,
                UserModel.is_deleted.is_(False)
            )
        )
        result = await db_conn.execute(query)
        return result.scalar_one_or_none()
