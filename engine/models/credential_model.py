from typing import TYPE_CHECKING
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    pass


class CredentialModel(BaseModel):
    __tablename__ = 'credentials'

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    salt: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    type: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True
    )
