from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.user_model import UserModel
from engine.models.role_model import RoleModel
from engine.models.workspace_model import WorkspaceModel
from engine.models.user_workspace_model import UserWorkspaceModel
from engine.repositories.user_repository import UserRepository
from engine.schemas.token_schemas import TokenData
from engine.services.base_service import BaseService
from engine.services.role_service import RoleService
from engine.services.user_credential_service import UserCredentialService
from engine.services.user_workspace_service import UserWorkspaceService
from engine.services.workspace_service import WorkspaceService
from engine.utils.generators_util import generate_timestamp_string


class UserService(BaseService[UserModel]):
    """
    UserService is a service that handles user management operations.

    Attributes:
        repository: UserRepository
        role_service: RoleService
        user_credentials_service: UserCredentialService
        user_workspace_service: UserWorkspaceService
        workspace_service: WorkspaceService

    Methods:    
        register: Register a new user.
        delete_user: Delete a user.
        
    """

    def __init__(self):
        self.repository: UserRepository = UserRepository()
        super().__init__(self.repository)
        self.role_service = RoleService()
        self.user_credentials_service = UserCredentialService()
        self.user_workspace_service = UserWorkspaceService()
        self.workspace_service = WorkspaceService()

    async def register(self, db_conn: AsyncSession, user_data: UserModel, password: str, workspace_id: UUID,
                            role_id: UUID, token_data: TokenData) -> Tuple[UserModel, RoleModel, WorkspaceModel]:
        if await self.repository.get_user_by_email(db_conn, user_data.email) or await self.repository.get_user_by_phone(
                db_conn, user_data.phone):
            raise Exception("already_exists")

        user = await self.create(db_conn, user_data)
        if not user:
            raise Exception("failed_to_create_user")

        role = await self.role_service.get_by_id(db_conn, role_id)
        workspace = await self.workspace_service.get_by_id(db_conn, workspace_id)

        if not role or not workspace:
            raise Exception("role_or_workspace_not_found")

        await self.user_credentials_service.create_user_credential(db_conn, user.id, password)

        user_workspace_data = UserWorkspaceModel(
            workspace_id=workspace_id,
            role_id=role_id,
            user_id=user.id,
            is_default=True
        )
        await self.user_workspace_service.create(db_conn, user_workspace_data)

        if token_data:
            await self.audit(db_conn, "user.register", {
                "id": str(token_data.user_id),
                "first_name": token_data.first_name,
                "last_name": token_data.last_name,
                "email": token_data.email
            }, {
                                 "id": str(user.id),
                                 "created_at": user.created_at,
                             })

        return user, role, workspace

    async def delete_user(
            self,
            db_conn: AsyncSession,
            uid: UUID,
            hard_delete: bool = False,
            token_data: Optional[TokenData] = None
    ) -> bool:
        try:
            user = await self.get_by_id(db_conn, uid)
            if not user:
                raise Exception("user_not_found")
            if hard_delete:
                # Perform hard delete
                await self.delete(db_conn, uid, hard_delete)
            else:
                # Perform soft delete with email/phone modification
                deleted_time_prefix = generate_timestamp_string()

                user.email = f"{deleted_time_prefix}{user.email}"
                user.phone = f"{deleted_time_prefix}{user.phone}" if user.phone else None
                user.is_deleted = True
                await self.update(db_conn, uid, user)

            if token_data:
                action = 'user.hard_deleted' if hard_delete else 'user.soft_deleted'
                await self.audit(db_conn, action, {
                    "id": str(token_data.user_id),
                    "first_name": token_data.first_name,
                    "last_name": token_data.last_name,
                    "email": token_data.email
                }, {
                                     "id": str(user.id),
                                     "first_name": user.first_name,
                                     "last_name": user.last_name,
                                     "email": user.email,
                                     "delete_type": "hard delete" if hard_delete else "soft delete"
                                 })

            return True

        except Exception as e:
            if token_data:
                await self.audit(db_conn, "user.failed_to_delete", {
                    "id": str(token_data.user_id),
                    "first_name": token_data.first_name,
                    "last_name": token_data.last_name,
                    "email": token_data.email
                }, {
                                     "error": str(e),
                                     "user_id": str(uid),
                                     "delete_type": "hard delete" if hard_delete else "soft delete"
                                 }, status="failed")
            raise e

