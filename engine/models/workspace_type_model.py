from typing import TYPE_CHECKING, List
from sqlalchemy import String, Text, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel

if TYPE_CHECKING:
    from .workspace_model import WorkspaceModel


class WorkspaceTypeModel(BaseModel):
    __tablename__ = "workspace_types"

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    is_system_defined: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        default=False,
        server_default="false"
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    workspaces: Mapped[List["WorkspaceModel"]] = relationship(
        "WorkspaceModel",
        back_populates="workspace_type",
        lazy="selectin",
        uselist=True
    )

    __table_args__ = (
        Index("idx_workspace_type_name", "name"),
    )
