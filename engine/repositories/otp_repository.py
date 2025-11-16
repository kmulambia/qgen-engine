from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from engine.models import OTPModel
from engine.repositories.base_repository import BaseRepository


class OTPRepository(BaseRepository[OTPModel]):
    def __init__(self):
        super().__init__(OTPModel)

    async def get_by_user_id(self, db_conn: AsyncSession, user_id: UUID) -> OTPModel:
        """
        Get an OTP by user ID.

        Args:
            db_conn (AsyncSession): The database connection.
            user_id (UUID): The user ID.

        Returns:
            OTPModel: The OTP model if found, otherwise None.
        """
        result = await db_conn.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.is_used is False)
            .order_by(self.model.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_active_otp(self, db_conn: AsyncSession, user_id: UUID, otp_type: str) -> OTPModel:
        """
        Get the active OTP for a user.

        Args:
            db_conn (AsyncSession): The database connection.
            user_id (UUID): The user ID.
            otp_type (str): The type of OTP.

        Returns:
            OTPModel: The active OTP if found, otherwise None.
        """
        result = await db_conn.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.otp_type == otp_type)
            .where(self.model.is_used is False)
            .where(self.model.expires_at > func.now())
            .order_by(self.model.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def deactivate_all_user_otp(self, db_conn: AsyncSession, user_id: UUID) -> None:
        """
        Deactivate all OTPs for a user.

        Args:
            db_conn (AsyncSession): The database connection.
            user_id (UUID): The user ID.
        """
        await db_conn.execute(
            self.model.__table__.update()  # Noqa
            .where(self.model.user_id == user_id)
            .where(self.model.is_used is False)
            .values(is_used=True, updated_at=func.now())
        )
