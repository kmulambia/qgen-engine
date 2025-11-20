from typing import Optional, TYPE_CHECKING
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import String, Text, ForeignKey, JSON, Index, Numeric, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .client_model import ClientModel
    from .layout_model import LayoutModel


class QuotationModel(BaseModel):
    """Model for storing quotations with line items and calculations"""
    __tablename__ = 'quotations'

    # Quotation Identifiers
    quotation_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        comment="Auto-generated unique quotation number (e.g., QT-2024-001)"
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Quotation title or subject"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the quotation"
    )

    # Client and Layout References
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Reference to the client"
    )

    layout_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("layouts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to the layout template"
    )

    # Line Items (JSON array of item objects)
    items: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Array of quotation line items with details"
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="Currency code (e.g., USD, EUR, GBP)"
    )

    # Financial Calculations
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=0.00,
        comment="Sum of all line item totals before tax and discount"
    )

    discount_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0.00,
        comment="Discount percentage (0-100)"
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=0.00,
        comment="Calculated discount amount"
    )

    tax_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0.00,
        comment="Tax percentage (e.g., VAT, GST)"
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=0.00,
        comment="Calculated tax amount"
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=0.00,
        comment="Final total: (subtotal - discount) + tax"
    )

    # Quotation Dates
    quotation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date when quotation was created/issued"
    )

    valid_until: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Quotation expiration date"
    )

    # Additional Information
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes about the quotation"
    )

    terms_conditions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Specific terms and conditions for this quotation"
    )

    # Quotation Status
    quotation_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        comment="Status: draft, sent, approved, rejected, expired"
    )

    # Email and Access Tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when quotation was sent to client"
    )

    access_token: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        index=True,
        comment="Secure token for public access to quotation"
    )

    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration timestamp for access token"
    )

    # Relationships
    client: Mapped["ClientModel"] = relationship(
        "ClientModel",
        lazy="selectin",
        foreign_keys=[client_id]
    )

    layout: Mapped[Optional["LayoutModel"]] = relationship(
        "LayoutModel",
        lazy="selectin",
        foreign_keys=[layout_id]
    )

    __table_args__ = (
        Index("idx_quotation_number", "quotation_number"),
        Index("idx_quotation_client_id", "client_id"),
        Index("idx_quotation_status", "quotation_status"),
        Index("idx_quotation_layout_id", "layout_id"),
        Index("idx_quotation_access_token", "access_token"),
    )

 