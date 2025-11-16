from datetime import date
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Date, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .user_workspace_model import UserWorkspaceModel
    from .token_model import TokenModel
    from .audit_model import AuditModel
    from .otp_model import OTPModel


class UserModel(BaseModel):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    phone: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )
    sex: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )
    id_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    id_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    user_workspaces: Mapped[List["UserWorkspaceModel"]] = relationship(
        "UserWorkspaceModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    tokens: Mapped[List["TokenModel"]] = relationship(
        "TokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    audits: Mapped[List["AuditModel"]] = relationship(
        "AuditModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    otps: Mapped[List["OTPModel"]] = relationship(
        "OTPModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_phone", "phone"),
        Index("idx_user_id_number", "id_number"),
    )
