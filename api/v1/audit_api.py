from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies.db import get_db
from api.v1.base_api import BaseAPI
from engine.models.audit_model import AuditModel
from engine.schemas.audit_schemas import (
    AuditSchema,
    AuditCreateSchema,
    AuditUpdateSchema,
    UserSecuritySummarySchema
)
from engine.schemas.base_schemas import PaginatedResponse
from engine.services.audit_service import AuditService
from engine.utils.config_util import load_config

config = load_config()
MODE = config.get_variable("MODE", "development")


class AuditAPI(BaseAPI[AuditModel, AuditCreateSchema, AuditUpdateSchema, PaginatedResponse[AuditSchema]]):
    def __init__(self):
        super().__init__(AuditService(), AuditSchema, AuditCreateSchema, AuditUpdateSchema, AuditModel,
                         PaginatedResponse[AuditSchema])

        # remove all routes except for the read endpoints
        self.router.routes = [
            route for route in self.router.routes
            if (route.path.endswith("/query") or
                (route.path == "" and "GET" in route.methods) or
                (route.path == "/{uid}" and "GET" in route.methods))
        ]

        # Add optimized endpoint for user security summary
        @self.router.get(
            "/users/{user_id}/security-summary",
            response_model=UserSecuritySummarySchema,
            summary="Get user security summary",
            description="Get comprehensive security information for a user in a single optimized query"
        )
        async def get_user_security_summary(
            user_id: UUID,
            session: AsyncSession = Depends(get_db)
        ):
            """
            Optimized endpoint that fetches all security-related audit data in one call:
            - Last successful login
            - Last password reset/change
            - Failed login attempts count (last 30 days)
            
            This replaces multiple separate queries with a single efficient call.
            """
            summary = await self.service.get_user_security_summary(user_id, session)
            
            return UserSecuritySummarySchema(
                last_login=AuditSchema.model_validate(summary["last_login"]) if summary["last_login"] else None,
                last_password_reset=AuditSchema.model_validate(summary["last_password_reset"]) if summary["last_password_reset"] else None,
                failed_login_count=summary["failed_login_count"]
            )


audit_api = AuditAPI()
router = audit_api.router

