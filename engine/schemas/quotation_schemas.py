from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema
from engine.schemas.client_schemas import ClientSchema
from engine.schemas.layout_schemas import LayoutSchema


class QuotationItemSchema(BaseModel):
    """Schema for individual quotation line items"""
    item_id: Optional[str] = Field(None, description="Optional item identifier")
    description: str = Field(..., min_length=1, description="Item description")
    quantity: Decimal = Field(..., gt=0, description="Item quantity")
    unit_price: Decimal = Field(..., ge=0, description="Price per unit")
    unit: Optional[str] = Field(default="unit", description="Unit of measurement (e.g., pcs, hrs, kg)")
    total: Optional[Decimal] = Field(None, description="Line total (quantity * unit_price)")
    notes: Optional[str] = Field(None, description="Additional notes for this item")

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def calculate_total(self):
        """Auto-calculate line item total"""
        if self.total is None:
            self.total = self.quantity * self.unit_price
        return self


class QuotationBaseSchema(BaseModel):
    """Base schema for quotation data"""
    title: str = Field(..., min_length=1, max_length=255, description="Quotation title")
    description: Optional[str] = Field(None, description="Detailed description")
    
    # References (Required)
    client_id: UUID = Field(..., description="Client ID")
    layout_id: UUID = Field(..., description="Layout template ID")
    
    # Dates (Required)
    quotation_date: date = Field(..., description="Quotation issue date")
    valid_until: date = Field(..., description="Quotation expiration date")
    
    # Line Items
    items: List[QuotationItemSchema] = Field(..., min_items=1, description="List of quotation items")
    
    # Financial fields
    discount_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Discount percentage")
    tax_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Tax percentage")
    
    # Additional Info
    notes: Optional[str] = Field(None, description="Internal notes")
    terms_conditions: Optional[str] = Field(None, description="Terms and conditions")
    quotation_status: str = Field(default="draft", description="Quotation status")

    model_config = ConfigDict(from_attributes=True)

    @field_validator('discount_percentage', 'tax_percentage', mode='before')
    @classmethod
    def validate_percentages(cls, v):
        """Ensure percentages are valid Decimals"""
        if v is None:
            return Decimal("0.00")
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_validator('quotation_status')
    @classmethod
    def validate_status(cls, v):
        """Validate quotation status"""
        valid_statuses = ['draft', 'sent', 'approved', 'rejected', 'expired', 'accepted']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class QuotationCreateSchema(QuotationBaseSchema, BaseCreateSchema):
    """Schema for creating a new quotation"""
    # quotation_number is auto-generated, not required on create
    # Calculated fields are optional on create - will be computed
    subtotal: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total: Optional[Decimal] = None


class QuotationUpdateSchema(BaseUpdateSchema):
    """Schema for updating an existing quotation"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    
    client_id: Optional[UUID] = None
    layout_id: Optional[UUID] = None
    
    quotation_date: Optional[date] = None
    valid_until: Optional[date] = None
    
    items: Optional[List[QuotationItemSchema]] = None
    
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    quotation_status: Optional[str] = None
    
    # Calculated fields are optional - will be recomputed
    subtotal: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total: Optional[Decimal] = None

    @field_validator('quotation_status')
    @classmethod
    def validate_status(cls, v):
        """Validate quotation status if provided"""
        if v is not None:
            valid_statuses = ['draft', 'sent', 'approved', 'rejected', 'expired', 'accepted']
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class QuotationSchema(BaseSchema):
    """Schema for quotation response including calculated fields and relationships"""
    quotation_number: Optional[str] = Field(None, description="Auto-generated quotation number")
    title: str
    description: Optional[str] = None
    
    client_id: UUID
    layout_id: UUID
    
    quotation_date: date
    valid_until: date
    
    items: List[QuotationItemSchema]
    
    # Calculated fields (required in response)
    subtotal: Decimal = Field(..., description="Subtotal before discount and tax")
    discount_percentage: Decimal
    discount_amount: Decimal = Field(..., description="Calculated discount amount")
    tax_percentage: Decimal
    tax_amount: Decimal = Field(..., description="Calculated tax amount")
    total: Decimal = Field(..., description="Final total amount")
    
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    quotation_status: str
    
    # Relationships
    client: Optional[ClientSchema] = Field(None, description="Client details")
    layout: Optional[LayoutSchema] = Field(None, description="Layout details")

    model_config = ConfigDict(from_attributes=True)


class QuotationCalculationResponse(BaseModel):
    """Response schema for calculation preview"""
    items: List[QuotationItemSchema]
    subtotal: Decimal
    discount_percentage: Decimal
    discount_amount: Decimal
    tax_percentage: Decimal
    tax_amount: Decimal
    total: Decimal
    breakdown: dict = Field(
        default_factory=dict,
        description="Detailed calculation breakdown"
    )

    model_config = ConfigDict(from_attributes=True)


def calculate_quotation_totals(
    items: List[QuotationItemSchema],
    discount_percentage: Decimal = Decimal("0.00"),
    tax_percentage: Decimal = Decimal("0.00")
) -> dict:
    """
    Calculate all quotation financial totals.
    
    Args:
        items: List of quotation items
        discount_percentage: Discount percentage (0-100)
        tax_percentage: Tax percentage (0-100)
    
    Returns:
        Dictionary with all calculated values
    """
    # Calculate subtotal from items
    subtotal = sum(item.total or (item.quantity * item.unit_price) for item in items)
    
    # Calculate discount
    discount_amount = (subtotal * discount_percentage) / Decimal("100")
    
    # Calculate amount after discount
    amount_after_discount = subtotal - discount_amount
    
    # Calculate tax on discounted amount
    tax_amount = (amount_after_discount * tax_percentage) / Decimal("100")
    
    # Calculate final total
    total = amount_after_discount + tax_amount
    
    return {
        "subtotal": round(subtotal, 2),
        "discount_percentage": discount_percentage,
        "discount_amount": round(discount_amount, 2),
        "tax_percentage": tax_percentage,
        "tax_amount": round(tax_amount, 2),
        "total": round(total, 2),
        "breakdown": {
            "items_total": round(subtotal, 2),
            "after_discount": round(amount_after_discount, 2),
            "tax_base": round(amount_after_discount, 2)
        }
    }
