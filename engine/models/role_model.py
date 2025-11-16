from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .role_permission_model import RolePermissionModel
    from .permission_model import PermissionModel
    from .user_workspace_model import UserWorkspaceModel


class RoleModel(BaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        unique=True
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    is_system_defined: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )

    role_permissions: Mapped[List["RolePermissionModel"]] = relationship(
        "RolePermissionModel",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    permissions: Mapped[List["PermissionModel"]] = relationship(
        "PermissionModel",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
        viewonly=True
    )
    user_workspaces: Mapped[List["UserWorkspaceModel"]] = relationship(
        "UserWorkspaceModel",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
