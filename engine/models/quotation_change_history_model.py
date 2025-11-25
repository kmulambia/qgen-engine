from typing import Optional, TYPE_CHECKING, Dict, Any
from uuid import UUID
from sqlalchemy import String, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .quotation_model import QuotationModel
    from .user_model import UserModel


class QuotationChangeHistoryModel(BaseModel):
    """Model for tracking detailed changes to quotations"""
    __tablename__ = 'quotation_change_history'

    # Foreign Keys
    quotation_id: Mapped[UUID] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the quotation that was changed"
    )

    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who made the change"
    )

    # Change Information
    change_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of change: created, updated, approved, resend, status_changed, items_modified"
    )

    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of the field that changed"
    )

    # Change Values (stored as JSON to handle complex types)
    from_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Previous value of the field (JSON format for complex types)"
    )

    to_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="New value of the field (JSON format for complex types)"
    )

    # Optional summary for batch changes
    change_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Optional summary of all changes in this transaction"
    )

    # Relationships
    quotation: Mapped["QuotationModel"] = relationship(
        "QuotationModel",
        lazy="selectin",
        foreign_keys=[quotation_id]
    )

    user: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        lazy="selectin",
        foreign_keys=[user_id]
    )

    __table_args__ = (
        Index("idx_quotation_change_history_quotation_id", "quotation_id"),
        Index("idx_quotation_change_history_user_id", "user_id"),
        Index("idx_quotation_change_history_created_at", "created_at"),
        Index("idx_quotation_change_history_change_type", "change_type"),
        Index("idx_quotation_change_history_quotation_created", "quotation_id", "created_at"),
    )

