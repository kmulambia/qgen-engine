from uuid import UUID
from typing import TYPE_CHECKING, List 
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel

if TYPE_CHECKING:
    from .workspace_type_model import WorkspaceTypeModel
    from .user_workspace_model import UserWorkspaceModel
    from .workspace_address_model import WorkspaceAddressModel
    from .address_model import AddressModel


class WorkspaceModel(BaseModel):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    workspace_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspace_types.id"),
        nullable=True
    )
    owner_id: Mapped[UUID] = mapped_column(
        nullable=True,
        comment="Reference to user who owns this workspace"
    )
    workspace_type: Mapped["WorkspaceTypeModel"] = relationship(
        "WorkspaceTypeModel",
        back_populates="workspaces",
        lazy="selectin",
        uselist=False
    )
    user_workspaces: Mapped[List["UserWorkspaceModel"]] = relationship(
        "UserWorkspaceModel",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    workspace_addresses: Mapped[List["WorkspaceAddressModel"]] = relationship(
        "WorkspaceAddressModel",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    addresses: Mapped[List["AddressModel"]] = relationship(
        "AddressModel",
        secondary="workspace_addresses",
        back_populates="workspaces",
        viewonly=True
    )
    __table_args__ = (
        Index("idx_workspace_owner", "owner_id"),
        Index("idx_workspace_type", "workspace_type_id"),
    )
