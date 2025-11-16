from datetime import datetime
from uuid import UUID
from typing import Optional, TYPE_CHECKING, Dict, Any, List
from sqlalchemy import JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from engine.models.approval_model import ApprovalModel
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .workflow_model import WorkflowModel
    from .workflow_stage_model import WorkflowStageModel
    from .user_model import UserModel
    from .workspace_model import WorkspaceModel
    from .attachment_model import AttachmentModel


class ApplicationModel(BaseModel):
    """Model representing an application going through workflow stages."""
    __tablename__ = "applications"
    # Metadata
    application_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default={}, nullable=True)
    workflow_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default={}, nullable=True)
    applicant_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default={}, nullable=True)
    workspace_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default={}, nullable=True)
    # Foreign Keys
    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("workflows.id"), nullable=False)
    workflow_stage_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workflow_stages.id"), nullable=True)
    applicant_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    applicant_workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    processed_by_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    processed_by_workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id"), nullable=True)
    # Timestamps
    submitted_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    completed_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    # Relationships
    workflow: Mapped["WorkflowModel"] = relationship(foreign_keys=[workflow_id], lazy="selectin")
    workflow_stage: Mapped[Optional["WorkflowStageModel"]] = relationship(foreign_keys=[workflow_stage_id],
                                                                          lazy="selectin")
    applicant: Mapped["UserModel"] = relationship(foreign_keys=[applicant_id], lazy="selectin")
    applicant_workspace: Mapped["WorkspaceModel"] = relationship(foreign_keys=[applicant_workspace_id], lazy="selectin")

    attachments: Mapped[List["AttachmentModel"]] = relationship(
        "AttachmentModel",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    approvals: Mapped[List["ApprovalModel"]] = relationship(
        "ApprovalModel",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    processed_by: Mapped[Optional["UserModel"]] = relationship(
        foreign_keys=[processed_by_id],
        lazy="selectin")
    processed_by_workspace: Mapped[Optional["WorkspaceModel"]] = relationship(
        foreign_keys=[processed_by_workspace_id],
        lazy="selectin")

    __table_args__ = (
        Index("idx_application_workflow", "workflow_id"),
        Index("idx_application_applicant", "applicant_id")
    )
