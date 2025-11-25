from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from engine.schemas.base_schemas import BaseSchema, BaseCreateSchema
from engine.schemas.user_schemas import UserSchema


class FieldChangeSchema(BaseModel):
    """Schema for individual field changes"""
    field_name: str = Field(..., description="Name of the field that changed")
    from_value: Optional[Dict[str, Any]] = Field(None, description="Previous value")
    to_value: Optional[Dict[str, Any]] = Field(None, description="New value")

    model_config = ConfigDict(from_attributes=True)


class QuotationChangeHistoryBaseSchema(BaseModel):
    """Base schema for quotation change history"""
    quotation_id: UUID = Field(..., description="ID of the quotation that was changed")
    user_id: Optional[UUID] = Field(None, description="ID of the user who made the change")
    change_type: str = Field(..., description="Type of change: created, updated, approved, etc.")
    field_name: str = Field(..., description="Name of the field that changed")
    from_value: Optional[Dict[str, Any]] = Field(None, description="Previous value (JSON format)")
    to_value: Optional[Dict[str, Any]] = Field(None, description="New value (JSON format)")
    change_summary: Optional[Dict[str, Any]] = Field(None, description="Optional summary of all changes")

    model_config = ConfigDict(from_attributes=True)


class QuotationChangeHistoryCreateSchema(QuotationChangeHistoryBaseSchema, BaseCreateSchema):
    """Schema for creating a change history record"""
    pass


class QuotationChangeHistorySchema(QuotationChangeHistoryBaseSchema, BaseSchema):
    """Schema for change history response including relationships"""
    user: Optional[UserSchema] = Field(None, description="User who made the change")

    model_config = ConfigDict(from_attributes=True)


class QuotationChangeHistoryListResponse(BaseModel):
    """Response schema for paginated change history list"""
    items: list[QuotationChangeHistorySchema] = Field(..., description="List of change history records")
    total: int = Field(..., description="Total number of records")
    limit: Optional[int] = Field(None, description="Maximum number of records returned")
    offset: Optional[int] = Field(None, description="Number of records skipped")

    model_config = ConfigDict(from_attributes=True)

