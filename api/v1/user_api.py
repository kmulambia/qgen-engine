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
    UserRegisterSchema,
    PaginatedResponse
)
from engine.schemas.token_schemas import TokenData
from engine.services.user_service import UserService
from engine.utils.config_util import load_config
from api.dependencies.mailer import send_email_message

config = load_config()
MODE = config.get_variable("MODE", "development")



class UserAPI(BaseAPI[UserModel, UserCreateSchema, UserUpdateSchema, UserSchema]):
    def __init__(self):
        self.service = UserService()
        super().__init__(self.service, UserSchema, UserCreateSchema, UserUpdateSchema, UserModel,
                         PaginatedResponse[UserSchema])

        # remove both the base POST/DELETE endpoints and the base delete by ID endpoint
        routes_to_remove = [
            route for route in self.router.routes
            if (route.path == "" and (route.methods == {"POST"} or route.methods == {"DELETE"})) or
               (route.path == "/{uid}" and route.methods == {"DELETE"})
        ]
        for route in routes_to_remove:
            self.router.routes.remove(route)

        @self.router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
        @rate_limit()
        async def delete_user(
                request: Request,
                uid: UUID,
                db: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication),
                hard_delete: bool = False
        ):
            try:
                return await self.service.delete_user(db_conn=db, uid=uid, hard_delete=hard_delete,
                                                      token_data=token_data)
            except Exception as e:
                logger.error(f"Failed to delete user: {e}, Request: {request.method} {request.url}")
                raise ErrorHandling.server_error("Failed to delete user")

        @self.router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
        @rate_limit()
        async def register(
                request: Request,
                data: UserRegisterSchema,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication),
        ):
            try:
                user_data = UserModel(**data.model_dump(exclude={'password', 'workspace_id', 'role_id'}))
                password = data.password
                workspace_id = data.workspace_id
                role_id = data.role_id

                # Register user and get user, role, and workspace data
                user, role, workspace = await self.service.register(
                    db_conn=db_conn,
                    user_data=user_data,
                    password=password,
                    workspace_id=workspace_id,
                    role_id=role_id,
                    token_data=token_data
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
                        f"User registration failed - already exists: {data.email}, Request: {request.method} {request.url}")
                    raise ErrorHandling.conflict("User with this email or phone already exists")

                elif error_message == "failed_to_create_user" or error_message == "role_or_workspace_not_found":
                    logger.error(
                        f"Failed to create user error: {error_message}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error("Failed to create user")
                else:
                    error_details = str(e) if MODE == "development" else "An error occurred while registering user."
                    logger.error(f"Unexpected error: {e}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error(error_details)






user_api = UserAPI()
router = user_api.router
