from uuid import UUID
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .role_model import RoleModel
    from .permission_model import PermissionModel


class RolePermissionModel(BaseModel):
    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False
    )

    role: Mapped["RoleModel"] = relationship(
        "RoleModel",
        back_populates="role_permissions",
        lazy="selectin",
        uselist=False
    )

    permission: Mapped["PermissionModel"] = relationship(
        "PermissionModel",
        back_populates="role_permissions",
        lazy="joined",
        uselist=False
    )
    __table_args__ = (
        Index("idx_role_permission_role_id", "role_id"),
        Index("idx_role_permission_permission_id", "permission_id"),
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission")
    )
