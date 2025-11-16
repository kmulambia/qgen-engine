from uuid import UUID
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .user_model import UserModel
    from .workspace_model import WorkspaceModel
    from .role_model import RoleModel


class UserWorkspaceModel(BaseModel):
    __tablename__ = "user_workspaces"

    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    workspace_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=True
    )
    is_default: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        default=False
    )
    role_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("roles.id"),
        nullable=True
    )
    workspace: Mapped["WorkspaceModel"] = relationship(
        "WorkspaceModel",
        lazy="selectin",
        back_populates="user_workspaces"
    )
    role: Mapped["RoleModel"] = relationship(
        "RoleModel",
        lazy="selectin",
        back_populates="user_workspaces"
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        lazy="selectin",
        back_populates="user_workspaces"
    )

    __table_args__ = (
        Index("idx_user_workspace_user_id", "user_id"),
        Index("idx_user_workspace_workspace_id", "workspace_id"),
        Index("idx_user_workspace_role_id", "role_id"),
        UniqueConstraint("user_id", "workspace_id", name="uq_user_workspace"),
        UniqueConstraint("user_id", "is_default", name="uq_default_user_workspace"),
    )
