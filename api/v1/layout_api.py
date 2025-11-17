from uuid import UUID
from fastapi import HTTPException, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies.db import get_db
from api.dependencies.authentication import authentication
from api.dependencies.error_handler import ErrorHandling
from api.dependencies.logging import logger
from api.dependencies.ratelimiter import rate_limit
from api.v1.base_api import BaseAPI
from engine.schemas.token_schemas import TokenData
from engine.schemas.layout_schemas import (
    LayoutSchema,
    LayoutCreateSchema,
    LayoutUpdateSchema
)
from engine.services.layout_service import LayoutService
from engine.models.layout_model import LayoutModel
from engine.schemas.base_schemas import PaginatedResponse


class LayoutAPI(BaseAPI[LayoutModel, LayoutCreateSchema, LayoutUpdateSchema, LayoutSchema]):
    def __init__(self):
        super().__init__(
            service=LayoutService(),
            response_model=LayoutSchema,
            create_schema=LayoutCreateSchema,
            update_schema=LayoutUpdateSchema,
            model_type=LayoutModel,
            paginated_response_model=PaginatedResponse[LayoutSchema]
        )
        
        @self.router.get("/default", response_model=LayoutSchema, status_code=status.HTTP_200_OK)
        @rate_limit()
        async def get_default_layout(
            request: Request,
            db_conn: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication)
        ):
            """
            Get the current default layout.
            """
            try:
                layout = await self.service.get_default_layout(db_conn)
                
                if not layout:
                    raise ErrorHandling.not_found("No default layout set")

                return LayoutSchema.model_validate(layout)

            except Exception as e:
                logger.error(f"Failed to get default layout: {str(e)}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to get default layout")


router = LayoutAPI().router
