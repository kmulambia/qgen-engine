from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class ClientBaseSchema(BaseModel):
    """Base schema for client data"""
    # Company Information
    company_name: str = Field(..., min_length=1, max_length=255, description="Legal name of the client company")
    registration_number: Optional[str] = Field(None, max_length=100, description="Company registration number")
    tax_id: Optional[str] = Field(None, max_length=100, description="Tax identification number")

    # Address Information
    address_line1: Optional[str] = Field(None, max_length=255, description="Primary address line")
    address_line2: Optional[str] = Field(None, max_length=255, description="Secondary address line")
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100, description="State/Province/Region")
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)

    # Company Contact Information
    phone: Optional[str] = Field(None, max_length=50, description="Main company phone number")
    email: Optional[EmailStr] = Field(None, description="Main company email address")
    website: Optional[str] = Field(None, max_length=255, description="Company website URL")

    # Contact Person Information
    contact_person_name: Optional[str] = Field(None, max_length=255, description="Primary contact person name")
    contact_person_email: Optional[EmailStr] = Field(None, description="Primary contact person email")
    contact_person_phone: Optional[str] = Field(None, max_length=50, description="Primary contact person phone")
    contact_person_position: Optional[str] = Field(None, max_length=100, description="Primary contact person position")

    # Additional Information
    notes: Optional[str] = Field(None, description="Additional notes about the client")

    model_config = ConfigDict(from_attributes=True)


class ClientCreateSchema(ClientBaseSchema, BaseCreateSchema):
    """Schema for creating a new client"""
    pass


class ClientUpdateSchema(BaseUpdateSchema):
    """Schema for updating an existing client"""
    # All fields are optional for updates
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)

    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)

    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)

    contact_person_name: Optional[str] = Field(None, max_length=255)
    contact_person_email: Optional[EmailStr] = None
    contact_person_phone: Optional[str] = Field(None, max_length=50)
    contact_person_position: Optional[str] = Field(None, max_length=100)

    notes: Optional[str] = None


class ClientSchema(ClientBaseSchema, BaseSchema):
    """Schema for client response"""
    pass
