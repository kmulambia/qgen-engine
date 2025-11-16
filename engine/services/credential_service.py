from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.credential_model import CredentialModel
from engine.repositories.credential_repository import CredentialRepository
from engine.services.base_service import BaseService
from engine.utils.encryption_util import encrypt, verify


class CredentialService(BaseService[CredentialModel]):
    """
    CredentialService is a service for managing credentials.
    
    Attributes:

    Methods:
        create_credential(self, password: str, credential_type: str = "bearers") -> Optional[CredentialModel]:
            Create a new credential.
        verify_credential(self, credential_id: UUID, password: str) -> bool:
            Verify a credential.
    """

    def __init__(self):
        super().__init__(CredentialRepository())

    async def create_credential(self, db_conn: AsyncSession, password: str, credential_type: str = "bearers") -> Optional[CredentialModel]:
        password_hash, salt = encrypt(password)
        credential = CredentialModel(
            password_hash=password_hash,
            type=credential_type,
            salt=salt
        )
        return await self.create(db_conn, credential)

    async def verify_credential(self, db_conn: AsyncSession, credential_id: UUID, password: str) -> bool:
        credential = await self.get_by_id(db_conn, credential_id)
        if not credential:
            return False
        return verify(password, credential.password_hash, credential.salt)
