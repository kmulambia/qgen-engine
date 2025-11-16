from uuid import UUID
from typing import Optional, TYPE_CHECKING, Dict, Any
from sqlalchemy import JSON, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .application_model import ApplicationModel
    from .workflow_model import WorkflowModel
    from .workflow_stage_model import WorkflowStageModel
    from .user_model import UserModel


class ApprovalModel(BaseModel):
    """Model representing approvals for applications at different workflow stages."""

    __tablename__ = "approvals"

    # Foreign Keys
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id"),
        nullable=False
    )
    workflow_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False
    )
    workflow_stage_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflow_stages.id"),
        nullable=False
    )
    approver_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    # Approval details
    decision: Mapped[str] = mapped_column(
        String(20),  # 'approved', 'rejected', 'pending'
        nullable=False,
        default='pending'
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    approval_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )

    # Relationships
    application: Mapped["ApplicationModel"] = relationship(
        foreign_keys=[application_id]
    )
    workflow: Mapped["WorkflowModel"] = relationship(
        foreign_keys=[workflow_id]
    )
    workflow_stage: Mapped["WorkflowStageModel"] = relationship(
        foreign_keys=[workflow_stage_id]
    )
    approver: Mapped["UserModel"] = relationship(
        foreign_keys=[approver_id]
    )

    __table_args__ = (
        Index("idx_approval_application", "application_id"),
        Index("idx_approval_workflow", "workflow_id"),
        Index("idx_approval_stage", "workflow_stage_id"),
        Index("idx_approval_approver", "approver_id"),
        Index("idx_approval_decision", "decision"),
    )
