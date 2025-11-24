from uuid import UUID
from fastapi import HTTPException, Depends, Request, status
from fastapi.responses import FileResponse
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
import os


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

        @self.router.get("/default/logo")
        @rate_limit()
        async def get_default_layout_logo(
            request: Request,
            db_conn: AsyncSession = Depends(get_db)
        ):
            """
            Get the logo file for the default layout.
            Returns the logo image file directly for frontend display.
            """
            try:
                layout = await self.service.get_default_layout(db_conn)
                
                if not layout:
                    raise ErrorHandling.not_found("No default layout set")

                if not layout.logo_file:
                    raise ErrorHandling.not_found("No logo file set for default layout")

                if not os.path.exists(layout.logo_file.full_path):
                    logger.error(f"Logo file not found on disk: {layout.logo_file.full_path}")
                    raise ErrorHandling.not_found("Logo file not found on disk")

                return FileResponse(
                    path=layout.logo_file.full_path,
                    media_type=layout.logo_file.content_type,
                    filename=layout.logo_file.original_filename
                )

            except Exception as e:
                logger.error(f"Failed to get default layout logo: {str(e)}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to get default layout logo")


router = LayoutAPI().router
