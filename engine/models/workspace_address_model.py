from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .workspace_model import WorkspaceModel
    from .address_model import AddressModel


class WorkspaceAddressModel(BaseModel):
    __tablename__ = 'workspace_addresses'

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey('workspaces.id'),
        nullable=True,
        index=True
    )
    address_id: Mapped[UUID] = mapped_column(
        ForeignKey('addresses.id'),
        nullable=True,
        index=True
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=True,
        server_default='false'
    )
    is_billing: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=True,
        server_default='false'
    )
    is_shipping: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=True,
        server_default='false'
    )

    workspace: Mapped["WorkspaceModel"] = relationship(
        "WorkspaceModel",
        back_populates="workspace_addresses",
        lazy="selectin"
    )
    address: Mapped["AddressModel"] = relationship(
        "AddressModel",
        back_populates="workspace_addresses",
        lazy="selectin"
    )

    __table_args__ = (
        Index('idx_workspace_addresses_workspace_id', 'workspace_id'),
        Index('idx_workspace_addresses_address_id', 'address_id'),
    )
