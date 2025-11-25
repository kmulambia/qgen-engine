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
from engine.utils.file_utils import save_uploaded_files, BASE_PATH
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
            if (route.path in ["", "/"] and "POST" in route.methods) or
               (route.path == "/{uid}" and "PUT" in route.methods) or
               (route.path == "/{uid}" and "DELETE" in route.methods)
        ]
        for route in routes_to_remove:
            self.router.routes.remove(route)

        @self.router.put("/{uid}", response_model=FileSchema, status_code=status.HTTP_200_OK)
        @rate_limit()
        async def update_file(
                request: Request,
                uid: UUID,
                file: UploadFile = File(...),
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication)
        ) -> FileSchema:
            """
            Update/replace an existing file by its ID.
            This will delete the old file from disk and upload the new one.
            """
            try:
                # Get existing file metadata
                existing_file = await self.service.get_by_id(db_conn, uid)
                if not existing_file:
                    raise ErrorHandling.not_found("File not found")

                # Read new file content
                content = await file.read()
                files_data = [{
                    "content": content,
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(content)
                }]

                # Save new file to disk
                uploaded_files = save_uploaded_files(files_data, None)
                if not uploaded_files:
                    raise ErrorHandling.server_error("Failed to save new file")

                uploaded_file = uploaded_files[0]

                # Delete old file from disk if it exists
                if os.path.exists(existing_file.full_path):
                    try:
                        os.remove(existing_file.full_path)
                    except Exception as e:
                        logger.error(f"Failed to delete old physical file: {str(e)}")
                        # Continue with update even if old file deletion fails

                # Update file metadata in database
                existing_file.filename = uploaded_file.name
                existing_file.original_filename = uploaded_file.original_filename
                existing_file.url = f"{request.base_url}{self.service.base_url}/serve/{uploaded_file.name}"
                existing_file.full_path = uploaded_file.full_path
                existing_file.content_type = uploaded_file.content_type
                existing_file.size = uploaded_file.size
                existing_file.file_modified_at = datetime.now(timezone.utc)

                updated_file = await self.service.update(db_conn, uid, existing_file, token_data)
                return FileSchema.model_validate(updated_file)

            except Exception as e:
                logger.error(f"Failed to update file: {str(e)}")
                if isinstance(e, HTTPException):
                    raise e
                raise ErrorHandling.server_error("Failed to update file")

        @self.router.post("", response_model=List[FileSchema], status_code=status.HTTP_201_CREATED)
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
                            url=f"{request.base_url}{self.service.base_url}/serve/{uploaded_file.name}",
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

        @self.router.get("/serve/{filename}")
        async def serve_file(
                request: Request,
                filename: str,
                db_conn: AsyncSession = Depends(get_db),
        ):
            """
            Serve a file by its filename (for direct URL access)
            Reconstructs path from BASE_PATH to be environment-agnostic
            """
            logger.debug(f"[FILE_SERVE] Request received for filename: {filename}")
            logger.debug(f"[FILE_SERVE] Request URL: {request.url}")
            logger.debug(f"[FILE_SERVE] BASE_PATH configured as: {BASE_PATH}")
            logger.debug(f"[FILE_SERVE] Current working directory: {os.getcwd()}")
            
            try:
                # Get file by filename
                from sqlalchemy import select
                from engine.models.file_model import FileModel
                
                logger.debug(f"[FILE_SERVE] Querying database for filename: {filename}")
                stmt = select(FileModel).where(FileModel.filename == filename)
                result = await db_conn.execute(stmt)
                file = result.scalar_one_or_none()
                
                if not file:
                    logger.error(f"[FILE_SERVE] File not found in database: {filename}")
                    raise ErrorHandling.not_found("File not found")

                logger.debug(f"[FILE_SERVE] File found in database. ID: {file.id}, stored full_path: {file.full_path}")
                logger.debug(f"[FILE_SERVE] File metadata - original_filename: {file.original_filename}, content_type: {file.content_type}")

                # Try multiple path resolution strategies
                file_path = None
                paths_to_try = []
                
                # Strategy 1: Reconstruct from BASE_PATH + filename (environment-agnostic)
                reconstructed_path = os.path.join(BASE_PATH, filename)
                paths_to_try.append(("BASE_PATH + filename", reconstructed_path))
                logger.debug(f"[FILE_SERVE] Strategy 1 - Reconstructed path: {reconstructed_path}")
                
                # Strategy 2: Use stored full_path (backward compatibility)
                paths_to_try.append(("stored full_path", file.full_path))
                logger.debug(f"[FILE_SERVE] Strategy 2 - Stored full_path: {file.full_path}")
                
                # Strategy 3: Extract directory from stored full_path and combine with filename
                if file.full_path:
                    stored_dir = os.path.dirname(file.full_path)
                    if stored_dir:
                        dir_based_path = os.path.join(stored_dir, filename)
                        paths_to_try.append(("stored_dir + filename", dir_based_path))
                        logger.debug(f"[FILE_SERVE] Strategy 3 - Extracted dir from stored path: {stored_dir}, combined path: {dir_based_path}")
                
                # Strategy 4: Try relative to current working directory
                cwd_path = os.path.join(os.getcwd(), BASE_PATH, filename)
                paths_to_try.append(("CWD + BASE_PATH + filename", cwd_path))
                logger.debug(f"[FILE_SERVE] Strategy 4 - CWD-based path: {cwd_path}")
                
                logger.debug(f"[FILE_SERVE] Starting path resolution - will try {len(paths_to_try)} strategies")
                
                # Try each path in order
                for idx, (strategy_name, path_to_check) in enumerate(paths_to_try, 1):
                    logger.debug(f"[FILE_SERVE] Strategy {idx}/{len(paths_to_try)} ({strategy_name}): Checking path: {path_to_check}")
                    
                    # Check if path exists
                    path_exists = os.path.exists(path_to_check)
                    logger.debug(f"[FILE_SERVE] Strategy {idx} - Path exists: {path_exists}")
                    
                    if path_exists:
                        # Check if it's a file
                        is_file = os.path.isfile(path_to_check)
                        logger.debug(f"[FILE_SERVE] Strategy {idx} - Is file: {is_file}")
                        
                        # Check if readable
                        is_readable = os.access(path_to_check, os.R_OK)
                        logger.debug(f"[FILE_SERVE] Strategy {idx} - Is readable: {is_readable}")
                        
                        if is_file and is_readable:
                            file_path = path_to_check
                            logger.info(f"[FILE_SERVE] ✓ File found using strategy {idx} ({strategy_name}): {path_to_check}")
                            break
                        else:
                            logger.warning(f"[FILE_SERVE] Strategy {idx} - Path exists but is_file={is_file}, readable={is_readable}")
                    else:
                        logger.debug(f"[FILE_SERVE] Strategy {idx} - Path does not exist")
                
                if not file_path:
                    # None of the paths exist - log detailed error with all attempted paths
                    logger.error(
                        f"[FILE_SERVE] ✗ File not found on disk. Filename: {filename}, "
                        f"BASE_PATH: {BASE_PATH}, "
                        f"Current working directory: {os.getcwd()}, "
                        f"Stored full_path: {file.full_path}, "
                        f"Attempted paths: {[f'{name}: {path} (exists={os.path.exists(path)})' for name, path in paths_to_try]}"
                    )
                    raise ErrorHandling.not_found("File not found on disk")

                logger.debug(f"[FILE_SERVE] Successfully resolved file path: {file_path}")
                logger.debug(f"[FILE_SERVE] Returning FileResponse with path: {file_path}, media_type: {file.content_type}")

                return FileResponse(
                    path=file_path,
                    media_type=file.content_type,
                    filename=file.original_filename
                )
            except HTTPException as e:
                logger.error(f"[FILE_SERVE] HTTPException: {e.status_code} - {e.detail}")
                raise e
            except Exception as e:
                logger.error(f"[FILE_SERVE] Unexpected error serving file '{filename}': {str(e)}", exc_info=True)
                raise ErrorHandling.server_error("Failed to serve file")

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
            Reconstructs path from BASE_PATH to be environment-agnostic
            """
            logger.debug(f"[FILE_DOWNLOAD] Request received for file ID: {uid}")
            logger.debug(f"[FILE_DOWNLOAD] Request URL: {request.url}")
            logger.debug(f"[FILE_DOWNLOAD] BASE_PATH configured as: {BASE_PATH}")
            logger.debug(f"[FILE_DOWNLOAD] Current working directory: {os.getcwd()}")
            
            try:
                logger.debug(f"[FILE_DOWNLOAD] Querying database for file ID: {uid}")
                file = await self.service.get_by_id(db_conn, uid)
                if not file:
                    logger.error(f"[FILE_DOWNLOAD] File not found in database: {uid}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("File not found")

                logger.debug(f"[FILE_DOWNLOAD] File found in database. Filename: {file.filename}, stored full_path: {file.full_path}")
                logger.debug(f"[FILE_DOWNLOAD] File metadata - original_filename: {file.original_filename}, content_type: {file.content_type}")

                # Try multiple path resolution strategies
                file_path = None
                paths_to_try = []
                
                # Strategy 1: Reconstruct from BASE_PATH + filename (environment-agnostic)
                reconstructed_path = os.path.join(BASE_PATH, file.filename)
                paths_to_try.append(("BASE_PATH + filename", reconstructed_path))
                logger.debug(f"[FILE_DOWNLOAD] Strategy 1 - Reconstructed path: {reconstructed_path}")
                
                # Strategy 2: Use stored full_path (backward compatibility)
                paths_to_try.append(("stored full_path", file.full_path))
                logger.debug(f"[FILE_DOWNLOAD] Strategy 2 - Stored full_path: {file.full_path}")
                
                # Strategy 3: Extract directory from stored full_path and combine with filename
                if file.full_path:
                    stored_dir = os.path.dirname(file.full_path)
                    if stored_dir:
                        dir_based_path = os.path.join(stored_dir, file.filename)
                        paths_to_try.append(("stored_dir + filename", dir_based_path))
                        logger.debug(f"[FILE_DOWNLOAD] Strategy 3 - Extracted dir from stored path: {stored_dir}, combined path: {dir_based_path}")
                
                # Strategy 4: Try relative to current working directory
                cwd_path = os.path.join(os.getcwd(), BASE_PATH, file.filename)
                paths_to_try.append(("CWD + BASE_PATH + filename", cwd_path))
                logger.debug(f"[FILE_DOWNLOAD] Strategy 4 - CWD-based path: {cwd_path}")
                
                logger.debug(f"[FILE_DOWNLOAD] Starting path resolution - will try {len(paths_to_try)} strategies")
                
                # Try each path in order
                for idx, (strategy_name, path_to_check) in enumerate(paths_to_try, 1):
                    logger.debug(f"[FILE_DOWNLOAD] Strategy {idx}/{len(paths_to_try)} ({strategy_name}): Checking path: {path_to_check}")
                    
                    # Check if path exists
                    path_exists = os.path.exists(path_to_check)
                    logger.debug(f"[FILE_DOWNLOAD] Strategy {idx} - Path exists: {path_exists}")
                    
                    if path_exists:
                        # Check if it's a file
                        is_file = os.path.isfile(path_to_check)
                        logger.debug(f"[FILE_DOWNLOAD] Strategy {idx} - Is file: {is_file}")
                        
                        # Check if readable
                        is_readable = os.access(path_to_check, os.R_OK)
                        logger.debug(f"[FILE_DOWNLOAD] Strategy {idx} - Is readable: {is_readable}")
                        
                        if is_file and is_readable:
                            file_path = path_to_check
                            logger.info(f"[FILE_DOWNLOAD] ✓ File found using strategy {idx} ({strategy_name}): {path_to_check}")
                            break
                        else:
                            logger.warning(f"[FILE_DOWNLOAD] Strategy {idx} - Path exists but is_file={is_file}, readable={is_readable}")
                    else:
                        logger.debug(f"[FILE_DOWNLOAD] Strategy {idx} - Path does not exist")
                
                if not file_path:
                    # None of the paths exist - log detailed error with all attempted paths
                    logger.error(
                        f"[FILE_DOWNLOAD] ✗ File not found on disk. File ID: {uid}, Filename: {file.filename}, "
                        f"BASE_PATH: {BASE_PATH}, "
                        f"Current working directory: {os.getcwd()}, "
                        f"Stored full_path: {file.full_path}, "
                        f"Attempted paths: {[f'{name}: {path} (exists={os.path.exists(path)})' for name, path in paths_to_try]}, "
                        f"Request: {request.method} {request.url}"
                    )
                    raise ErrorHandling.not_found("File not found on disk")

                logger.debug(f"[FILE_DOWNLOAD] Successfully resolved file path: {file_path}")
                logger.debug(f"[FILE_DOWNLOAD] Returning FileResponse with path: {file_path}, media_type: {file.content_type}")

                return FileResponse(
                    path=file_path,
                    media_type=file.content_type,
                    filename=file.filename
                )
            except HTTPException as e:
                logger.error(f"[FILE_DOWNLOAD] HTTPException: {e.status_code} - {e.detail}")
                raise e
            except Exception as e:
                logger.error(f"[FILE_DOWNLOAD] Unexpected error downloading file '{uid}': {str(e)}, Request: {request.method} {request.url}", exc_info=True)
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
