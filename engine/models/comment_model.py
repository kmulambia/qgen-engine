from uuid import UUID
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .user_model import UserModel
    from .workflow_model import WorkflowModel
    from .workflow_stage_model import WorkflowStageModel
    from .application_model import ApplicationModel


class CommentModel(BaseModel):
    """Model for storing comments across different entities in the system."""

    __tablename__ = "comments"

    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    recipient_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(nullable=True)
    message: Mapped[str] = mapped_column(nullable=True)
    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("workflows.id"), nullable=True)
    workflow_stage_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_stages.id"), nullable=True)
    application_id: Mapped[UUID] = mapped_column(ForeignKey("applications.id"), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=True)

    # Relationships

    sender: Mapped["UserModel"] = relationship(foreign_keys=[sender_id], lazy="selectin")
    recipient: Mapped["UserModel"] = relationship(foreign_keys=[recipient_id], lazy="selectin")
    workflow: Mapped["WorkflowModel"] = relationship(foreign_keys=[workflow_id], lazy="selectin")
    workflow_stage: Mapped["WorkflowStageModel"] = relationship(foreign_keys=[workflow_stage_id], lazy="selectin")
    application: Mapped["ApplicationModel"] = relationship(foreign_keys=[application_id], lazy="selectin")
