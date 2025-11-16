from uuid import UUID
from typing import TYPE_CHECKING, Optional, Dict, Any
from sqlalchemy import ForeignKey, JSON, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .application_model import ApplicationModel
    from .file_model import FileModel
    from .workflow_model import WorkflowModel
    from .workflow_stage_model import WorkflowStageModel
    from .user_model import UserModel


class AttachmentModel(BaseModel):
    """Model representing the relationship between applications and files with reference details."""

    __tablename__ = "attachments"

    # Foreign Keys
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False
    )

    workflow_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False
    )

    workflow_stage_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflow_stages.id", ondelete="CASCADE"),
        nullable=False
    )

    file_id: Mapped[UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False
    )

    uploaded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    attachment_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )

    # Relationships
    application: Mapped["ApplicationModel"] = relationship(
        "ApplicationModel",
        back_populates="attachments",
        lazy="selectin"
    )
    workflow: Mapped["WorkflowModel"] = relationship(
        "WorkflowModel",
        lazy="selectin"
    )
    workflow_stage: Mapped["WorkflowStageModel"] = relationship(
        "WorkflowStageModel",
        lazy="selectin"
    )
    file: Mapped["FileModel"] = relationship(
        "FileModel",
        lazy="selectin"
    )
    uploader: Mapped["UserModel"] = relationship(
        "UserModel",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_attachment_application_id", "application_id"),
        Index("idx_attachment_file_id", "file_id"),
        Index("idx_attachment_reference", "name"),
    )
