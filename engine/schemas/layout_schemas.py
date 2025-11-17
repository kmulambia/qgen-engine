from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema
from engine.schemas.file_schemas import FileSchema


class LayoutBaseSchema(BaseModel):
    """Base schema for layout with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Unique name for the layout")
    description: Optional[str] = Field(None, description="Description of the layout")
    
    # Logo
    logo_file_id: Optional[UUID] = Field(None, description="ID of the logo file")
    
    # Contract information
    contract_name: Optional[str] = Field(None, max_length=255, description="Contract contact name")
    contract_number: Optional[str] = Field(None, max_length=100, description="Contract number")
    contract_email: Optional[str] = Field(None, max_length=255, description="Contract email address")
    contract_phone: Optional[str] = Field(None, max_length=50, description="Contract phone number")
    contract_address: Optional[str] = Field(None, description="Contract physical address")
    
    # Terms and conditions
    terms_conditions: Optional[str] = Field(None, description="Terms and conditions text")
    
    # Notes
    notes: Optional[str] = Field(None, description="Additional notes or instructions")
    
    # Links
    links: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Dictionary of links (e.g., {'website': 'https://example.com', 'support': 'https://support.example.com'})"
    )
    
    # Custom fields for extensibility
    custom_fields: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional custom fields for specific use cases"
    )
    
    # Default flag
    is_default: bool = Field(default=False, description="Whether this is the default layout")

    model_config = ConfigDict(from_attributes=True)

    @field_validator('contract_email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided"""
        if v is not None and v.strip():
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v


class LayoutCreateSchema(LayoutBaseSchema, BaseCreateSchema):
    """Schema for creating a new layout"""
    pass


class LayoutUpdateSchema(BaseUpdateSchema):
    """Schema for updating an existing layout"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    logo_file_id: Optional[UUID] = None
    contract_name: Optional[str] = Field(None, max_length=255)
    contract_number: Optional[str] = Field(None, max_length=100)
    contract_email: Optional[str] = Field(None, max_length=255)
    contract_phone: Optional[str] = Field(None, max_length=50)
    contract_address: Optional[str] = None
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None
    links: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None

    @field_validator('contract_email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided"""
        if v is not None and v.strip():
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v


class LayoutSchema(LayoutBaseSchema, BaseSchema):
    """Schema for layout response including related data"""
    logo_file: Optional[FileSchema] = Field(None, description="Logo file details")

    model_config = ConfigDict(from_attributes=True)


class LayoutLogoUploadResponse(BaseModel):
    """Response schema for logo upload"""
    layout_id: UUID
    logo_file_id: UUID
    logo_url: str
    message: str = "Logo uploaded successfully"

    model_config = ConfigDict(from_attributes=True)
