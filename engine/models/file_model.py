from typing import Optional
from sqlalchemy import Text, String,  DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from engine.models.base_model import BaseModel
from datetime import datetime


class FileModel(BaseModel):
    """Model for storing file metadata and references"""
    __tablename__ = 'files'

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    full_path: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    file_modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )   
    file_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )
    checksum: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    storage_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="local"
    )
    file_metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    __table_args__ = (
        # Add any indexes here if needed
    )
