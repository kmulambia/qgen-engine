from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Text, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .workspace_address_model import WorkspaceAddressModel
    from .workspace_model import WorkspaceModel


class AddressModel(BaseModel):
    __tablename__ = 'addresses'

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    address_line_1: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    address_line_2: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    address_line_3: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    country: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    province: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    city: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    physical: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    postal: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    workspace_addresses: Mapped[List["WorkspaceAddressModel"]] = relationship(
        "WorkspaceAddressModel",
        back_populates='address',
        cascade='all, delete-orphan',
        lazy='selectin'
    )
    workspaces: Mapped[List["WorkspaceModel"]] = relationship(
        "WorkspaceModel",
        secondary='workspace_addresses',
        back_populates='addresses',
        lazy='selectin',
        viewonly=True
    )

    __table_args__ = (
        Index('idx_address_name', 'name', postgresql_where=(name.isnot(None))),
        Index('idx_address_country', 'country'),
        Index('idx_address_city_province', 'city', 'province'),
    )
