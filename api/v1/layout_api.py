from uuid import UUID
from typing import List
from fastapi import UploadFile, File, HTTPException, Depends, Request, status
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
    LayoutUpdateSchema,
    LayoutLogoUploadResponse
)
from engine.services.layout_service import LayoutService
from engine.services.file_service import FileService
from engine.models.layout_model import LayoutModel
from engine.models.file_model import FileModel
from engine.schemas.base_schemas import PaginatedResponse
from engine.utils.file_utils import save_uploaded_files
from datetime import datetime, timezone


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
        
        self.file_service = FileService()
        self.file_service.base_url = "api/v1/files"

        @self.router.post("/{uid}/logo", response_model=LayoutLogoUploadResponse, status_code=status.HTTP_200_OK)
        @rate_limit()
        async def upload_logo(
            request: Request,
            uid: UUID,
            file: UploadFile = File(...),
            db_conn: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication)
        ) -> LayoutLogoUploadResponse:
            """
            Upload or update the logo for a layout.
            Only accepts image files (jpg, jpeg, png, gif, svg, webp).
            """
            try:
                # Validate layout exists
                layout = await self.service.get_by_id(db_conn, uid)
                if not layout:
                    raise ErrorHandling.not_found("Layout not found")

                # Validate file type
                allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/svg+xml", "image/webp"]
                if file.content_type not in allowed_types:
                    raise ErrorHandling.invalid_request(
                        f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
                    )

                # Read file content
                content = await file.read()
                if len(content) > 5 * 1024 * 1024:  # 5MB limit
                    raise ErrorHandling.invalid_request("File size exceeds 5MB limit")

                files_data = [{
                    "content": content,
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(content)
                }]

                # Save file to disk
                uploaded_files = save_uploaded_files(files_data, "logos")
                
                if not uploaded_files:
                    raise ErrorHandling.server_error("Failed to save logo file")

                uploaded_file = uploaded_files[0]

                # Save file metadata to database
                file_data = FileModel(
                    filename=uploaded_file.name,
                    original_filename=uploaded_file.original_filename,
                    url=f"{request.base_url}{self.file_service.base_url}{uploaded_file.url}",
                    full_path=uploaded_file.full_path,
                    content_type=uploaded_file.content_type,
                    size=uploaded_file.size,
                    file_created_at=datetime.now(timezone.utc),
                    file_modified_at=datetime.now(timezone.utc),
                )
                saved_file = await self.file_service.create(db_conn, file_data, token_data)

                # Update layout with new logo
                updated_layout = await self.service.update_logo(
                    db_conn,
                    uid,
                    saved_file.id,
                    token_data
                )

                return LayoutLogoUploadResponse(
                    layout_id=updated_layout.id,
                    logo_file_id=saved_file.id,
                    logo_url=saved_file.url
                )

            except Exception as e:
                logger.error(f"Failed to upload logo: {str(e)}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to upload logo")

        @self.router.delete("/{uid}/logo", status_code=status.HTTP_200_OK)
        @rate_limit()
        async def remove_logo(
            request: Request,
            uid: UUID,
            db_conn: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication)
        ):
            """
            Remove the logo from a layout.
            """
            try:
                # Validate layout exists
                layout = await self.service.get_by_id(db_conn, uid)
                if not layout:
                    raise ErrorHandling.not_found("Layout not found")

                if not layout.logo_file_id:
                    raise ErrorHandling.invalid_request("Layout has no logo to remove")

                # Remove logo reference from layout
                updated_layout = await self.service.remove_logo(db_conn, uid, token_data)

                return {
                    "message": "Logo removed successfully",
                    "layout_id": str(updated_layout.id)
                }

            except Exception as e:
                logger.error(f"Failed to remove logo: {str(e)}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to remove logo")

        @self.router.post("/{uid}/set-default", response_model=LayoutSchema, status_code=status.HTTP_200_OK)
        @rate_limit()
        async def set_default_layout(
            request: Request,
            uid: UUID,
            db_conn: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication)
        ) -> LayoutSchema:
            """
            Set a layout as the default layout.
            Only one layout can be default at a time.
            """
            try:
                # Validate layout exists
                layout = await self.service.get_by_id(db_conn, uid)
                if not layout:
                    raise ErrorHandling.not_found("Layout not found")

                # Set as default
                updated_layout = await self.service.set_default_layout(db_conn, uid, token_data)

                return LayoutSchema.model_validate(updated_layout)

            except Exception as e:
                logger.error(f"Failed to set default layout: {str(e)}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to set default layout")

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
