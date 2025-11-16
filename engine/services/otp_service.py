from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from engine.models import UserModel
from engine.models.otp_model import OTPModel
from engine.repositories.otp_repository import OTPRepository
from engine.services.base_service import BaseService
from engine.utils.encryption_util import encrypt, verify
from engine.utils.generators_util import generate_random_string


class OTPService(BaseService[OTPModel]):
    """
    OTPService is a service for managing OTPs.

    Attributes:
        repository: OTPRepository

    Methods:
        get_by_user_id: Get an OTP by user ID.
        generate_otp: Generate a new OTP.
        verify_otp: Verify an OTP code.
        get_active_otp: Get the active OTP for a user.
    """

    def __init__(self):
        repository = OTPRepository()
        super().__init__(repository)
        self.repository = repository

    async def get_by_user_id(self, db_conn: AsyncSession, user_id: UUID) -> Optional[OTPModel]:
        """
        Get an OTP by user ID.

        Args:
            db_conn (AsyncSession): The database connection.
            user_id (UUID): The user ID.

        Returns:
            Optional[OTPModel]: The OTP model if found, otherwise None.
        """
        return await self.repository.get_by_user_id(db_conn, user_id)

    async def get_active_otp(self, db_conn: AsyncSession, user_id: UUID, otp_type: str) -> Optional[OTPModel]:
        """
        Get the active OTP for a user.

        Args:
            db_conn (AsyncSession): The database connection.
            user_id (UUID): The user ID.
            otp_type (str): The type of OTP.

        Returns:
            Optional[OTPModel]: The active OTP if found and not expired, otherwise None.
        """
        otp = await self.repository.get_active_otp(db_conn, user_id, otp_type)
        if otp and otp.expires_at > datetime.now(otp.expires_at.tzinfo):
            return otp
        return None

    async def generate_otp(self, db_conn: AsyncSession, user: UserModel, otp_type: str = 'password-reset') -> Tuple[OTPModel, str]:
        """
        Generate a new OTP.

        Args:
            db_conn (AsyncSession): The database connection.
            user (UserModel): The user model.
            otp_type (str): The type of OTP.

        Returns:
            Tuple[OTPModel, str]: The created OTP model and the plain text code.
        """
        # Check for existing active OTP
        existing_otp = await self.repository.get_active_otp(db_conn, user.id, otp_type)
        if existing_otp:
            # Use custom exception instead of ErrorHandling
            raise Exception("active_otp_already_exists")

        # Generate new OTP
        code = generate_random_string(6)
        code_hash, salt = encrypt(code)

        # Set expiration to 10 minutes from now
        expires_at = datetime.now() + timedelta(minutes=10)

        otp = OTPModel(
            user_id=user.id,
            otp_type=otp_type,
            code_hash=code_hash,
            salt=salt,
            expires_at=expires_at
        )

        await self.repository.deactivate_all_user_otp(db_conn, user.id)

        created_otp = await self.create(db_conn, otp)

        if created_otp:
            await self.audit(db_conn, f"otp.request.{otp_type}", {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            }, {
                                 "id": str(created_otp.id),
                                 "created_at": created_otp.created_at,
                                 "otp_type": otp_type,
                                 "expires_at": expires_at.isoformat()
                             })

        return created_otp, code

    async def verify_otp(self, db_conn: AsyncSession, user_id: UUID, code: str,
                         otp_type: Optional[str] = 'password-reset') -> bool:
        """
        Verify the OTP.

        Args:
            db_conn (AsyncSession): The database connection.
            user_id (UUID): The user ID.
            code (str): The OTP code to verify.
            token_data (Optional[TokenData]): Token data for audit logging.

        Returns:
            bool: True if the OTP is valid, False otherwise.
            :param db_conn:
            :param user_id:
            :param code:
            :param otp_type:
        """
        otp = await self.get_active_otp(db_conn, user_id, otp_type)
        if not otp:
            return False

        # Check if OTP is expired
        if otp.expires_at <= datetime.now(otp.expires_at.tzinfo):
            return False

        # Verify the code
        is_verified = verify(code, otp.code_hash, otp.salt)

        if is_verified:
            otp.is_used = True
            await self.update(db_conn, uid=otp.id, data=otp)

            await self.audit(db_conn, "otp.verify", {
                "id": str(user_id),
                "otp_id": str(otp.id)
            }, {
                                 "verified": True,
                                 "expires_at": otp.expires_at.isoformat()
                             })

        return is_verified
