from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .role_permission_model import RolePermissionModel
    from .role_model import RoleModel


class PermissionModel(BaseModel):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    group: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )

    role_permissions: Mapped[List["RolePermissionModel"]] = relationship(
        "RolePermissionModel",
        back_populates="permission",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    roles: Mapped[List["RoleModel"]] = relationship(
        "RoleModel",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
        viewonly=True
    )

    __table_args__ = (
        Index("idx_permission_code", "code"),
        Index("idx_permission_name", "name"),
        Index("idx_permission_group", "group"),
    )
