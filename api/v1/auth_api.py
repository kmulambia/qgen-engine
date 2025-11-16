from uuid import UUID
from fastapi import Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies.authentication import authentication
from api.dependencies.db import get_db
from api.dependencies.error_handler import ErrorHandling
from api.dependencies.logging import logger
from api.dependencies.ratelimiter import rate_limit
from api.v1.base_api import BaseAPI
from engine.models.user_model import UserModel
from engine.schemas import (
    UserCreateSchema,
    UserUpdateSchema,
    UserSchema,
    SelfRegisterSchema,
    LoginSchema,
    PaginatedResponse,
    SessionSchema,
    SessionUserSchema,
    SessionTokenSchema,
    SessionUserWorkspaceSchema,
    SessionWorkspaceSchema,
    SessionRoleSchema,
    SessionPermissionSchema,
    SessionWorkspaceTypeSchema, 
    PasswordChangeSchema
)
from engine.schemas.token_schemas import TokenData
from engine.services.auth_service import AuthService
from engine.utils.config_util import load_config
from api.dependencies.mailer import send_email_message
from engine.schemas import OTPRequestSchema, PasswordResetSchema

config = load_config()
MODE = config.get_variable("MODE", "development")


class AuthAPI(BaseAPI[UserModel, UserCreateSchema, UserUpdateSchema, UserSchema]):
    def __init__(self):
        self.service = AuthService()
        super().__init__(self.service, UserSchema, UserCreateSchema, UserUpdateSchema, UserModel,
                         PaginatedResponse[UserSchema])

        # Remove all base CRUD endpoints since this is auth-specific
        routes_to_remove = [
            route for route in self.router.routes
            if route.path in ["", "/{uid}","/count","/query"] and route.methods in [{"GET"}, {"POST"}, {"PUT"}, {"DELETE"}]
        ]
        for route in routes_to_remove:
            self.router.routes.remove(route)

        @self.router.post("/self-register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
        @rate_limit()
        async def self_register(
                request: Request,
                data: SelfRegisterSchema,
                db_conn: AsyncSession = Depends(get_db)
        ):
            try:
                # Call AuthService.self_register which delegates to UserService.register with defaults
                user, role, workspace = await self.service.self_register(
                    db_conn=db_conn,
                    data=data
                )

                # **** Welcome email ****
                email_message = {
                    "template": {
                        "name": "registration",
                        "data": {
                            "user": {
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "email": user.email
                            },
                            "role": {
                                "name": role.name,
                            },
                            "workspace": {
                                "name": workspace.name,
                            },
                            "subject": f"Welcome to {config.require_variable('NAME')}",
                            "system_name": config.require_variable("NAME"),
                            "support_email": config.require_variable("EMAIL")
                        }
                    }
                }
                await send_email_message(email_message)
                # **** End of welcome email ****
                return user

            except Exception as e:
                error_message = str(e)
                if error_message == "already_exists":
                    logger.error(
                        f"Self-registration failed - already exists: {data.email}, Request: {request.method} {request.url}")
                    raise ErrorHandling.conflict("User with this email or phone already exists")
                elif error_message in ["default_role_not_found", "default_workspace_not_found"]:
                    logger.error(
                        f"Self-registration failed - configuration error: {error_message}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error("Self-registration configuration error")
                elif error_message == "failed_to_create_user":
                    logger.error(
                        f"Self-registration failed - user creation error: {error_message}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error("Failed to create user")
                else:
                    error_details = str(e) if MODE == "development" else "An error occurred during self-registration."
                    logger.error(f"Self-registration failed: {e}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error(error_details)

        @self.router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
        @rate_limit()
        async def change_password(
                request: Request,
                data: PasswordChangeSchema,
                db: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication),
        ):
            try:
                user = await self.service.change_user_credentials(db_conn=db, user_id=data.user_id,
                                                                  password=data.password, token_data=token_data)
                # **** Security email notification ****
                email_message = {
                    "template": {
                        "name": "password_change",
                        "data": {
                            "user": {
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "email": user.email
                            },
                            "subject": "Password Changed",
                            "system_name": config.require_variable("NAME"),
                            "support_email": config.require_variable("EMAIL")
                        }
                    }
                }
                await send_email_message(email_message)
                # **** End of security email notification ****

                return None
            except Exception as e:
                error_message = str(e)
                if error_message == "user_not_found":
                    logger.error(f"Failed to change password: {error_message}, Request: {request.method} {request.url}")
                    raise ErrorHandling.bad_request(" Failed to change password something went wrong")
                else:
                    logger.error(f"Failed to change password: {error_message}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error("Unexpected error occurred during changing password")

        @self.router.post("/login", response_model=SessionSchema)
        @rate_limit()
        async def login(
                request: Request,
                data: LoginSchema,
                db_conn: AsyncSession = Depends(get_db)
        ):
            try:

                token, user, role, user_workspace, role_permissions, user_workspaces = await self.service.login(
                    db_conn=db_conn,
                    email=data.email,
                    password=data.password,
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent")
                )

                return SessionSchema(
                    user=SessionUserSchema(
                        id=user.id,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email
                    ),
                    token=SessionTokenSchema(
                        jwt_token=token.jwt_token,
                        token_type=token.token_type,
                        expires_at=token.expires_at
                    ),
                    current_workspace=SessionUserWorkspaceSchema(
                        id=user_workspace.id,
                        workspace=SessionWorkspaceSchema(
                            id=user_workspace.workspace.id,
                            name=user_workspace.workspace.name,
                            description=user_workspace.workspace.description,
                            workspace_type=SessionWorkspaceTypeSchema(
                                id=user_workspace.workspace.workspace_type.id,
                                name=user_workspace.workspace.workspace_type.name,
                                description=user_workspace.workspace.workspace_type.description
                            ) if user_workspace.workspace.workspace_type else None
                        )
                    ),
                    role=SessionRoleSchema(
                        id=role.id,
                        name=role.name,
                        description=role.description,
                        is_system_defined=role.is_system_defined
                    ),
                    permissions=[
                        SessionPermissionSchema(
                            id=rp.permission.id,
                            name=rp.permission.name,
                            description=rp.permission.description,
                            group=rp.permission.group,
                            code=rp.permission.code
                        ) for rp in role_permissions
                    ],
                    user_workspaces=[
                        SessionUserWorkspaceSchema(
                            id=uw.id,
                            workspace=SessionWorkspaceSchema(
                                id=uw.workspace.id,
                                name=uw.workspace.name,
                                description=uw.workspace.description,
                                workspace_type=SessionWorkspaceTypeSchema(
                                    id=uw.workspace.workspace_type.id,
                                    name=uw.workspace.workspace_type.name,
                                    description=uw.workspace.workspace_type.description
                                ) if uw.workspace.workspace_type else None
                            )
                        ) for uw in user_workspaces
                    ]
                )

            except Exception as e:
                error_message = str(e)
                if error_message in ["user_not_found", "invalid_credentials", "user_workspace_not_found",
                                     "role_not_found"]:
                    logger.error(f"Login failed - with error: {error_message}, Request: {request.method} {request.url}")
                    raise ErrorHandling.invalid_credentials("Invalid email or password")
                if error_message == "user_not_active":
                    logger.error(
                        f"Login failed - user not active: {data.email}, Request: {request.method} {request.url}")
                    raise ErrorHandling.forbidden("User account is not active")
                else:
                    logger.error(f"Unexpected error during login: {str(e)}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error("An unexpected error occurred during login")

        @self.router.post("/request-otp", status_code=status.HTTP_200_OK)
        @rate_limit()
        async def request_otp(
                request: Request,
                data: OTPRequestSchema,
                db_conn: AsyncSession = Depends(get_db)
        ):
            try:
                # Generate OTP
                user, code = await self.service.request_otp(
                    db_conn=db_conn,
                    email=data.email,
                    otp_type=data.otp_type,
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent")
                )

                # Send email with OTP
                email_message = {
                    "template": {
                        "name": "otp_code",
                        "data": {
                            "user": {
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "email": user.email
                            },
                            "otp_code": code,
                            "otp_type": data.otp_type,
                            "system_name": config.require_variable("NAME"),
                            "support_email": config.require_variable("EMAIL"),
                            "subject": f"Your {data.otp_type.replace('_', ' ').title()} Verification Code"
                        }
                    }
                }
                await send_email_message(email_message)

                return {"message": "OTP sent successfully"}

            except Exception as e:
                error_message = str(e)
                if error_message == "user_not_found":
                    logger.error(
                        f"OTP request failed - user not found: {data.email}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("User not found")
                elif error_message == "user_not_active":
                    logger.error(
                        f"OTP request failed - user not active: {data.email}, Request: {request.method} {request.url}")
                    raise ErrorHandling.forbidden("User account is not active")
                elif error_message == "active_otp_already_exists":
                    logger.error(
                        f"OTP request failed - OTP service error: Active OTP already exists, Request: {request.method} {request.url}")
                    raise ErrorHandling.forbidden("Invalid OTP")
                else:
                    logger.error(f"Failed to request OTP: {error_message}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error("Failed to request OTP")

        @self.router.post("/reset-password", status_code=status.HTTP_200_OK)
        @rate_limit()
        async def reset_password(
                request: Request,
                data: PasswordResetSchema,
                db_conn: AsyncSession = Depends(get_db)
        ):
            try:
                # Verify OTP and change password
                user = await self.service.verify_otp_and_change_password(
                    db_conn=db_conn,
                    email=data.email,
                    code=data.code,
                    new_password=data.new_password,
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent")
                )

                if not user:
                    logger.error(
                        f"Failed to reset password: User not found or invalid OTP, Request: {request.method} {request.url}")
                    raise ErrorHandling.bad_request("Invalid verification code or user not found")

                # Send confirmation email
                email_message = {
                    "template": {
                        "name": "password_change",
                        "data": {
                            "user": {
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "email": user.email
                            },
                            "system_name": config.require_variable("NAME"),
                            "support_email": config.require_variable("EMAIL")
                        }
                    }
                }
                await send_email_message(email_message)

                return {"message": "Password reset successfully"}

            except Exception as e:
                error_message = str(e)
                if error_message == "invalid_otp":
                    logger.error(
                        f"Password reset failed - invalid OTP: {data.email}, Request: {request.method} {request.url}")
                    raise ErrorHandling.bad_request("Invalid verification code")
                elif error_message == "user_not_found":
                    logger.error(
                        f"Password reset failed - user not found: {data.email}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("User not found")
                else:
                    logger.error(f"Failed to reset password: {error_message}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error("Failed to reset password")


auth_api = AuthAPI()
router = auth_api.router
