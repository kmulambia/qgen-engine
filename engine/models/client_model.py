from typing import Optional
from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base_model import BaseModel


class ClientModel(BaseModel):
    __tablename__ = "clients"

    # Company Information
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Legal name of the client company"
    )

    registration_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Company registration/incorporation number"
    )

    tax_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Tax identification number (e.g., VAT, EIN)"
    )

    # Address Information
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Primary address line"
    )

    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Secondary address line"
    )

    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="State/Province/Region"
    )

    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )

    # Company Contact Information
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Main company phone number"
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Main company email address"
    )

    website: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Company website URL"
    )

    # Contact Person Information (Primary Point of Contact)
    contact_person_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Name of the primary contact person"
    )

    contact_person_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Email of the primary contact person for quotations"
    )

    contact_person_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Phone number of the primary contact person"
    )

    contact_person_position: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Job title/position of the primary contact person"
    )

    # Additional Information
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes or comments about the client"
    )

    __table_args__ = (
        Index("idx_client_company_name", "company_name"),
        Index("idx_client_registration_number", "registration_number"),
        Index("idx_client_email", "email"),
        Index("idx_client_contact_email", "contact_person_email"),
    )

    @classmethod
    def get_unique_identifier_field(cls):
        """
        Returns the company_name as the unique identifier for versioning.
        """
        return cls.company_name
