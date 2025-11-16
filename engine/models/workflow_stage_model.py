from uuid import UUID
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from engine.models.base_model import BaseModel
if TYPE_CHECKING:
    from .workflow_model import WorkflowModel
    from .permission_model import PermissionModel


class WorkflowStageModel(BaseModel):
    """Model representing a stage in a workflow."""
    
    __tablename__ = "workflow_stages"

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(default=None)
    sequence: Mapped[int] = mapped_column(nullable=False)
    type: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    permission_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("permissions.id"), nullable=True)
    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("workflows.id"), nullable=False)
    # Relationships
    workflow: Mapped["WorkflowModel"] = relationship(
        back_populates="stages",
        lazy="selectin"
    )
    permission: Mapped[Optional["PermissionModel"]] = relationship(
        "PermissionModel",
        foreign_keys=[permission_id],
        lazy="selectin"
    )
    __table_args__ = (
        Index("idx_workflow_stage_workflow_name", "name"),
        Index("idx_workflow_stage_workflow_sequence", "sequence"),
    )

  