from uuid import UUID
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Boolean, Index, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .user_model import UserModel


class OTPModel(BaseModel):
    __tablename__ = "otp"
    """Model for storing OTP (One-Time Password) information"""
    
    code_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    salt: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    otp_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        lazy="selectin",
        back_populates="otps"
    )
    __table_args__ = (
        Index("idx_otp_code_hash", "code_hash"),
        Index("idx_otp_user_id", "user_id"),
        Index("idx_otp_type", "otp_type"),
    )
