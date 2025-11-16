from typing import Optional, Tuple, List
from uuid import UUID
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.user_model import UserModel
from engine.models.role_model import RoleModel
from engine.models.token_model import TokenModel
from engine.models.user_workspace_model import UserWorkspaceModel
from engine.models.role_permission_model import RolePermissionModel
from engine.models.workspace_model import WorkspaceModel
from engine.repositories.user_repository import UserRepository
from engine.schemas.token_schemas import TokenData
from engine.schemas.auth_schemas import SelfRegisterSchema
from engine.services.base_service import BaseService
from engine.services.role_service import RoleService
from engine.services.role_permission_service import RolePermissionService
from engine.services.token_service import TokenService
from engine.services.user_credential_service import UserCredentialService
from engine.services.user_workspace_service import UserWorkspaceService
from engine.services.workspace_service import WorkspaceService
from engine.services.workspace_type_service import WorkspaceTypeService
from engine.services.otp_service import OTPService
from engine.services.user_service import UserService


class AuthService(BaseService[UserModel]):
    """
    AuthService handles authentication-related operations.

    Attributes:
        repository: UserRepository
        user_credentials_service: UserCredentialService
        role_service: RoleService
        role_permission_service: RolePermissionService
        user_workspace_service: UserWorkspaceService
        workspace_service: WorkspaceService
        workspace_type_service: WorkspaceTypeService
        token_service: TokenService
        otp_service: OTPService

    Methods:    
        self_register: Self-register a new user with default role.
        login: Login a user.
        change_user_credentials: Change a user's credentials.
        request_otp: Request OTP for password reset.
        verify_otp_and_change_password: Verify OTP and change password.
    """

    def __init__(self):
        self.repository: UserRepository = UserRepository()
        super().__init__(self.repository)
        self.user_service = UserService()
        self.user_credentials_service = UserCredentialService()
        self.role_service = RoleService()
        self.role_permission_service = RolePermissionService()
        self.user_workspace_service = UserWorkspaceService()
        self.workspace_service = WorkspaceService()
        self.workspace_type_service = WorkspaceTypeService()
        self.token_service = TokenService()
        self.otp_service = OTPService()

    async def self_register(self, db_conn: AsyncSession, data: SelfRegisterSchema) -> Tuple[UserModel, RoleModel, WorkspaceModel]:
        """
        Self-register a new user with default role and workspace.
        This method calls the UserService.register method with default values.
        """
        try:
            # Get default role (assuming "User" is the default role for self-registration)
            default_role = await self.role_service.get_by_name(db_conn, "User")
            if not default_role:
                raise Exception("default_role_not_found")

            # Get default workspace (assuming there's a default workspace for self-registration)
            # You might need to adjust this based on your business logic
            default_workspace = await self.workspace_service.get_by_name(db_conn, "Default")
            if not default_workspace:
                raise Exception("default_workspace_not_found")

            # Create user data from SelfRegisterSchema
            user_data = UserModel(
                first_name=data.first_name,
                last_name=data.last_name,
                phone=data.phone,
                email=data.email,
                sex=data.sex,
                id_number=data.id_number,
                id_type=data.id_type,
                date_of_birth=data.date_of_birth
            )

            # Call UserService.register with default role and workspace
            user, role, workspace = await self.user_service.register(
                db_conn=db_conn,
                user_data=user_data,
                password=data.password,
                workspace_id=default_workspace.id,
                role_id=default_role.id,
                token_data=None  # No token data for self-registration
            )

            # Audit successful self-registration
            await self.audit(db_conn, "user.self_register", {
                "email": data.email,
                "first_name": data.first_name,
                "last_name": data.last_name
            }, {
                "id": str(user.id),
                "created_at": user.created_at,
                "role": role.name,
                "workspace": workspace.name
            })

            return user, role, workspace

        except Exception as e:
            # Audit the failure
            await self.audit(db_conn, "user.self_register_failed", {
                "email": data.email,
                "error": str(e)
            }, {
                "error": str(e)
            }, status="failed")
            raise e

    async def login(
            self,
            db_conn: AsyncSession,
            email: EmailStr,
            password: str,
            workspace_id: str = None,
            ip_address: str = None,
            user_agent: str = None
    ) -> Tuple[TokenModel, UserModel, RoleModel, UserWorkspaceModel, List[RolePermissionModel], List[UserWorkspaceModel]]:
        try:

            user = await self.repository.get_user_by_email(db_conn, str(email))
            if not user:
                raise Exception("user_not_found")
            if user.status != "active":
                raise Exception("user_not_active")
            if not await self.user_credentials_service.verify_user_credential(db_conn=db_conn, user_id=user.id, password=password):
                raise Exception("invalid_credentials")

            if workspace_id:
                user_workspace = await self.user_workspace_service.get_user_workspace_by_id(db_conn=db_conn,
                                                                                            workspace_id=UUID(
                                                                                                workspace_id),
                                                                                            user_id=user.id)
                if not user_workspace:
                    raise Exception("user_workspace_not_found")
                if user_workspace.status != "active":
                    raise Exception("user_workspace_not_active")
                else:
                    pass
            else:
                # Get the default user workspace
                user_workspace = await self.user_workspace_service.get_default_user_workspace(db_conn=db_conn,
                                                                                              user_id=user.id)

            if not user_workspace:
                raise Exception("user_workspace_not_found")

            role = await self.role_service.get_by_id(db_conn=db_conn, uid=user_workspace.role_id)

            if not role:
                raise Exception("role_not_found")

            user_workspaces = await self.user_workspace_service.get_user_workspaces(db_conn=db_conn, user_id=user.id)
            role_permissions = await self.role_permission_service.get_by_role_id(db_conn=db_conn, role_id=role.id)

            token = await self.token_service.generate(
                db_conn=db_conn,
                user=user,
                role_id=role.id,
                workspace_id=user_workspace.workspace_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            if token:
                await self.audit(db_conn, "user.login", {
                    "id": str(user.id),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                }, {
                    "id": str(user.id),
                    "created_at": user.created_at,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                })

            return token, user, role, user_workspace, role_permissions, user_workspaces

        except Exception as e:
            await self.audit(db_conn, "user.login", None, {
                "email": email,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "error": str(e)
            }, status="failed")
            raise e

    async def change_user_credentials(self, db_conn: AsyncSession, user_id: UUID, password: str,
                                      token_data: TokenData) -> UserModel:
        try:
            user = await self.repository.get_by_id(db_conn, user_id)
            if not user:
                raise Exception("user_not_found")
            await self.user_credentials_service.create_user_credential(db_conn, user_id, password)
            if token_data:
                action = 'user.password_change' if user_id == token_data.user_id else 'user.password_change_by_admin'
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
                                     "created_at": user.created_at,
                                 })
            return user
        except Exception as e:
            await self.audit(db_conn, "user.failed_to_change_user_credentials",
                             {
                                 "id": str(token_data.user_id),
                                 "first_name": token_data.first_name,
                                 "last_name": token_data.last_name,
                                 "email": token_data.email
                             }, {
                                 "comment": "Failed to change user credentials",
                                 "ip_address": token_data.ip_address,
                                 "user_agent": token_data.user_agent,
                                 "error": str(e)
                             }, status="failed")
            raise e

    async def request_otp(
            self,
            db_conn: AsyncSession,
            email: EmailStr,
            otp_type: str,
            ip_address: str = None,
            user_agent: str = None
    ) -> Tuple[UserModel, str]:
        try:
            user = await self.repository.get_user_by_email(db_conn, str(email))

            if not user:
                raise Exception("user_not_found")
            if user.status != "active":
                raise Exception("user_not_active")

            # Generate OTP and send it to the user's email
            otp, code = await self.otp_service.generate_otp(db_conn, user, otp_type)

            if otp:
                await self.audit(db_conn, "user.request_otp", {
                    "id": str(user.id),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email
                }, {
                                     "ip_address": ip_address,
                                     "user_agent": user_agent
                                 })

            return user, code

        except Exception as e:
            await self.audit(db_conn, "user.failed_to_request_otp", {
                "email": email,
                "ip_address": ip_address,
                "user_agent": user_agent
            }, {
                                 "error": str(e)
                             }, status="failed")
            raise e

    async def verify_otp_and_change_password(
            self,
            db_conn: AsyncSession,
            email: EmailStr,
            code: str,
            new_password: str,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> UserModel:
        try:
            user = await self.repository.get_user_by_email(db_conn, str(email))
            if not user:
                raise Exception("user_not_found")

            # Verify OTP
            is_verified = await self.otp_service.verify_otp(db_conn, user.id, code)
            if not is_verified:
                raise Exception("invalid_otp")

            # Change password
            await self.user_credentials_service.create_user_credential(db_conn, user.id, new_password)

            # Audit the password change
            await self.audit(db_conn, "user.password_reset", {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            }, {
                                 "ip_address": ip_address,
                                 "user_agent": user_agent
                             })

            return user

        except Exception as e:
            error_message = str(e)
            # Create a safe audit data structure
            audit_data = {
                "email": email,
                "error": error_message
            }

            # Audit the failure
            await self.audit(db_conn, "user.failed_to_verify_otp", None, audit_data, status="failed")

            # Re-raise the exception to be handled by the API layer
            raise e
