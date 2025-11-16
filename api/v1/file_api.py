from uuid import UUID
from typing import List
from fastapi import UploadFile, File, HTTPException, Depends, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies.db import get_db
from api.dependencies.authentication import authentication
from api.dependencies.error_handler import ErrorHandling
from api.dependencies.logging import logger
from api.dependencies.ratelimiter import rate_limit
from api.v1.base_api import BaseAPI
from engine.schemas.token_schemas import TokenData
from engine.schemas.file_schemas import FileSchema, FileCreateSchema, FileUpdateSchema
from engine.services.file_service import FileService
from engine.models.file_model import FileModel
from engine.schemas.base_schemas import PaginatedResponse
from engine.utils.config_util import load_config
from engine.utils.file_utils import save_uploaded_files
from datetime import datetime, timezone

import os

config = load_config()
MODE = config.get_variable("MODE", "development")


class FileAPI(BaseAPI[FileModel, FileCreateSchema, FileUpdateSchema, FileSchema]):
    def __init__(self):
        super().__init__(
            service=FileService(),
            response_model=FileSchema,
            create_schema=FileCreateSchema,
            update_schema=FileUpdateSchema,
            model_type=FileModel,
            paginated_response_model=PaginatedResponse[FileSchema]
        )

        self.service.base_url = f"api/v1/files"

        # Remove default POST, PUT, and DELETE endpoints
        routes_to_remove = [
            route for route in self.router.routes
            if (route.path == "" and route.methods == {"POST"}) or
               (route.path == "/{uid}" and route.methods == {"PUT"}) or
               (route.path == "/{uid}" and route.methods == {"DELETE"})
        ]
        for route in routes_to_remove:
            self.router.routes.remove(route)

        @self.router.post("/", response_model=List[FileSchema], status_code=status.HTTP_201_CREATED)
        @rate_limit()
        async def upload_files(
                request: Request,
                files: List[UploadFile] = File(...),
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication)
        ) -> List[FileSchema]:
            files_data = []

            try:
                if not files:
                    raise ErrorHandling.invalid_request("No files to upload")

                # Read file content
                for file in files:
                    content = await file.read()
                    files_data.append({
                        "content": content,
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": len(content)
                    })

                uploaded_files = save_uploaded_files(files_data, None)
                result_files = []

                # Save file metadata to database
                for uploaded_file in uploaded_files:
                    try:
                        # NOTE: file_metadata is not used in the database
                        file_data = FileModel(
                            filename=uploaded_file.name,  # Map name to filename
                            original_filename=uploaded_file.original_filename,
                            url=f"{request.base_url}{self.service.base_url}{uploaded_file.url}",
                            full_path=uploaded_file.full_path,
                            content_type=uploaded_file.content_type,
                            size=uploaded_file.size,
                            file_created_at=datetime.now(timezone.utc),
                            file_modified_at=datetime.now(timezone.utc),
                        )
                        saved_file = await self.service.create(db_conn, file_data, token_data)
                        result_files.append(FileSchema.model_validate(saved_file))
                    except Exception as e:
                        logger.error(f"Failed to upload file files : {str(e)}")
                        continue

                if not result_files:
                    raise ErrorHandling.server_error("Failed to upload any files")

                return result_files
            except Exception as e:
                logger.error(f"Failed to process file upload: {str(e)}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to process file upload")

        @self.router.get("/{uid}/download")
        @rate_limit()
        async def download_file(
                request: Request,
                uid: UUID,
                db_conn: AsyncSession = Depends(get_db),
                # token_data: TokenData = Depends(authentication)
        ):
            """
            Download a file by its ID
            """
            try:
                file = await self.service.get_by_id(db_conn, uid)
                if not file:
                    logger.error(f"File not found: {uid}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("File not found")

                if not os.path.exists(file.full_path):
                    logger.error(f"File not found on disk: {file.full_path}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("File not found on disk")

                return FileResponse(
                    path=file.full_path,
                    media_type=file.content_type,
                    filename=file.filename
                )
            except Exception as e:
                logger.error(f"Failed to download file: {str(e)}, Request: {request.method} {request.url}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to download file")

        @self.router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
        @rate_limit()
        async def delete_file(
                request: Request,
                uid: UUID,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication),
                hard_delete: bool = False
        ):
            """
            Delete a file by its ID with option for hard delete
            """
            try:
                file = await self.service.get_by_id(db_conn, uid)
                if not file:
                    raise ErrorHandling.not_found("File not found")

                # Delete physical file if exists
                if os.path.exists(file.full_path):
                    try:
                        os.remove(file.full_path)
                    except Exception as e:
                        logger.error(f"Failed to delete physical file: {str(e)}")
                        raise ErrorHandling.server_error("Failed to delete physical file")

                # Delete from database
                await self.service.delete(db_conn, uid, hard_delete, token_data)
                return {"message": "File deleted successfully"}
            except Exception as e:
                logger.error(f"Failed to delete file: {str(e)}, Request: {request.method} {request.url}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to delete file")


router = FileAPI().router
