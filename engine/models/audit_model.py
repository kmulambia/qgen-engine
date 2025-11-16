from uuid import UUID
from typing import TYPE_CHECKING, Optional, Any, Dict
from sqlalchemy import JSON, String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .user_model import UserModel


class AuditModel(BaseModel):
    __tablename__ = "audits"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    user_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(512),
        nullable=False
    )
    entity_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="audits",
        lazy="selectin"
    )

    __table_args__ = (
        # Optimized indexes for common queries
        Index("idx_audit_user_id", "user_id", postgresql_where="user_id IS NOT NULL"),
        Index("idx_audit_user_action_created", "user_id", "action", "created_at"),
        Index("idx_audit_action_status_created", "action", "status", "created_at"),
        Index("idx_audit_created_at", "created_at"),
    )
