from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class FileBaseSchema(BaseModel):
    filename: str
    original_filename: str
    url: str
    # full_path: str
    content_type: str
    size: int
    checksum: Optional[str] = None
    storage_provider: str = "local"
    # file_metadata: Optional[str] = None
    file_created_at: datetime
    file_modified_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileCreateSchema(FileBaseSchema, BaseCreateSchema):
    pass


class FileUpdateSchema(FileBaseSchema, BaseUpdateSchema):
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    url: Optional[str] = None
    full_path: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None


class FileSchema(FileBaseSchema, BaseSchema):
    pass


class FileMetadata(BaseModel):
    """Schema for file metadata response"""
    name: str = Field(..., description="Generated unique filename using ISO datetime stamp")
    original_filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="URL path to the file")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="Size of file in bytes")
    created_at: float = Field(..., description="File creation timestamp")
    modified_at: float = Field(..., description="File last modification timestamp")
    full_path: str = Field(..., description="Full path to file")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "2024-03-15T14-30-45-123.pdf",
                "original_filename": "document.pdf",
                "url": "documents/2024-03-15T14-30-45-123.pdf",
                "content_type": "application/pdf",
                "size": 1024,
                "created_at": 1677721600.0,
                "modified_at": 1677721600.0
            }
        }


class MultipleFileUploadSchema(BaseModel):
    """Schema for handling multiple file uploads"""
    files: list[FileCreateSchema] = Field(..., description="List of files to upload")

    class Config:
        json_schema_extra = {
            "example": {
                "files": [
                    {
                        "filename": "2024-03-15T14-30-45-123.pdf",
                        "original_filename": "document1.pdf",
                        "url": "documents/2024-03-15T14-30-45-123.pdf",
                        "full_path": "/var/www/uploads/documents/2024-03-15T14-30-45-123.pdf",
                        "content_type": "application/pdf",
                        "size": 1024,
                        "storage_provider": "local"
                    },
                    {
                        "filename": "2024-03-15T14-30-46-456.jpg",
                        "original_filename": "image1.jpg",
                        "url": "images/2024-03-15T14-30-46-456.jpg",
                        "content_type": "image/jpeg",
                        "size": 2048,
                        "storage_provider": "local"
                    }
                ]
            }
        }


class MultipleFileResponseSchema(BaseModel):
    """Schema for multiple file upload response"""
    files: list[FileMetadata] = Field(..., description="List of uploaded file metadata")
    total_count: int = Field(..., description="Total number of files uploaded")
    total_size: int = Field(..., description="Total size of all uploaded files in bytes")

    class Config:
        json_schema_extra = {
            "example": {
                "files": [
                    {
                        "name": "2024-03-15T14-30-45-123.pdf",
                        "original_filename": "document1.pdf",
                        "url": "documents/2024-03-15T14-30-45-123.pdf",
                        "content_type": "application/pdf",
                        "size": 1024,
                        "created_at": 1677721600.0,
                        "modified_at": 1677721600.0
                    },
                    {
                        "name": "2024-03-15T14-30-46-456.jpg",
                        "original_filename": "image1.jpg",
                        "url": "images/2024-03-15T14-30-46-456.jpg",
                        "content_type": "image/jpeg",
                        "size": 2048,
                        "created_at": 1677721600.0,
                        "modified_at": 1677721600.0
                    }
                ],
                "total_count": 2,
                "total_size": 3072
            }
        }
