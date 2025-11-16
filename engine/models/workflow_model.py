from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy import ForeignKey, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .workflow_stage_model import WorkflowStageModel
    from .application_model import ApplicationModel
    from .workspace_model import WorkspaceModel


class WorkflowModel(BaseModel):
    __tablename__ = "workflows"
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    component: Mapped[str] = mapped_column(default=None, nullable=True)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    expiry_in_days: Mapped[int] = mapped_column(default=30)
    workspace: Mapped["WorkspaceModel"] = relationship(foreign_keys=[workspace_id], lazy="selectin")

    stages: Mapped[List["WorkflowStageModel"]] = relationship(
        "WorkflowStageModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    applications: Mapped[List["ApplicationModel"]] = relationship(
        "ApplicationModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
