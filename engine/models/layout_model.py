from typing import Optional, TYPE_CHECKING
from uuid import UUID
from sqlalchemy import String, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .file_model import FileModel


class LayoutModel(BaseModel):
    """Model for storing quotation layout configuration templates"""
    __tablename__ = 'layouts'

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Logo file reference
    logo_file_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True
    )

    # Contract information
    contract_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    contract_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    contract_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    contract_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    contract_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Terms and conditions
    terms_conditions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Links as JSON array for flexibility
    links: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )

    # Additional custom fields as JSON for extensibility
    custom_fields: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )

    # Whether this is the default layout
    is_default: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false"
    )

    # Relationships
    logo_file: Mapped[Optional["FileModel"]] = relationship(
        "FileModel",
        lazy="selectin",
        foreign_keys=[logo_file_id]
    )

    __table_args__ = (
        Index("idx_layout_name", "name"),
        Index("idx_layout_is_default", "is_default"),
    )
