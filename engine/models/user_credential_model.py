from uuid import UUID
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .user_model import UserModel
    from .credential_model import CredentialModel


class UserCredentialModel(BaseModel):
    __tablename__ = "user_credentials"

    credential_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("credentials.id", ondelete="CASCADE"),
        nullable=True
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        lazy="selectin"
    )
    credential: Mapped["CredentialModel"] = relationship(
        "CredentialModel",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_user_credential_user_id", "user_id"),
        Index("idx_user_credential_credential_id", "credential_id"),
    )
