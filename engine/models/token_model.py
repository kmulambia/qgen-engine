from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .user_model import UserModel


class TokenModel(BaseModel):
    __tablename__ = "tokens"

    jwt_token: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        unique=True,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    token_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 addresses can be up to 45 characters
        nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["UserModel"] = relationship(
        back_populates="tokens",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_token_user_id", "user_id"),
        Index("idx_token_jwt_token", "jwt_token"),
    )
