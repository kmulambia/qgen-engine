from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.user_credential_model import UserCredentialModel
from engine.repositories.user_credential_repository import UserCredentialRepository
from engine.services.base_service import BaseService
from engine.services.credential_service import CredentialService


class UserCredentialService(BaseService[UserCredentialModel]):
    """
    UserCredentialService is a service that handles user credentials.

    Attributes:
        credential_service: CredentialService

    Methods:
        create_user_credential: Create a new user credential.
        verify_user_credential: Verify a user credential.
        
    """

    def __init__(self):
        self.repository: UserCredentialRepository = UserCredentialRepository()
        super().__init__(UserCredentialRepository())
        self.credential_service = CredentialService()

    async def create_user_credential(self, db_conn: AsyncSession, user_id: UUID, password: str,
                                     credential_type: str = "bearers") -> Optional[UserCredentialModel]:
        await self.repository.deactivate_all_user_credentials(db_conn, user_id)
        credential = await self.credential_service.create_credential(db_conn, password, credential_type)
        return await self.create(db_conn, UserCredentialModel(user_id=user_id, credential_id=UUID(str(credential.id)),
                                                              status="active"))

    async def verify_user_credential(self, db_conn: AsyncSession, user_id: UUID, password: str) -> bool:
        user_credential = await self.repository.get_latest_user_credential(db_conn, user_id)
        
        print(f"the user is {user_credential}")
        if not user_credential:
            return False
        return await self.credential_service.verify_credential(db_conn, user_credential.credential_id, password)
