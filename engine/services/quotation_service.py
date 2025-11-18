from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.quotation_model import QuotationModel
from engine.repositories.quotation_repository import QuotationRepository
from engine.services.base_service import BaseService
from engine.schemas.quotation_schemas import calculate_quotation_totals, QuotationItemSchema
from engine.schemas.token_schemas import TokenData


class QuotationService(BaseService[QuotationModel]):
    def __init__(self):
        super().__init__(QuotationRepository())
    
    def _generate_quotation_number(self) -> str:
        """Generate a unique quotation number"""
        # Format: QT-YYYY-NNNN (e.g., QT-2024-0001)
        current_year = datetime.now().year
        # In production, you'd query the database to get the next sequence number
        # For now, using timestamp-based generation
        timestamp = datetime.now().strftime("%m%d%H%M%S")
        return f"QT-{current_year}-{timestamp}"
    
    def _calculate_and_update_totals(self, quotation_data: dict) -> dict:
        """
        Calculate all financial totals and update the quotation data.
        
        Args:
            quotation_data: Dictionary with quotation data
            
        Returns:
            Updated quotation data with calculated totals
        """
        # Get items from the data
        items_data = quotation_data.get('items', [])
        
        # Convert to QuotationItemSchema for validation and calculation
        items = []
        for item_data in items_data:
            if isinstance(item_data, dict):
                items.append(QuotationItemSchema(**item_data))
            else:
                items.append(item_data)
        
        # Get discount and tax percentages
        discount_percentage = quotation_data.get('discount_percentage', Decimal("0.00"))
        tax_percentage = quotation_data.get('tax_percentage', Decimal("0.00"))
        
        # Convert to Decimal if needed
        if isinstance(discount_percentage, (int, float)):
            discount_percentage = Decimal(str(discount_percentage))
        if isinstance(tax_percentage, (int, float)):
            tax_percentage = Decimal(str(tax_percentage))
        
        # Calculate totals
        calculations = calculate_quotation_totals(
            items=items,
            discount_percentage=discount_percentage,
            tax_percentage=tax_percentage
        )
        
        # Update the quotation data with calculated values
        quotation_data['subtotal'] = calculations['subtotal']
        quotation_data['discount_amount'] = calculations['discount_amount']
        quotation_data['tax_amount'] = calculations['tax_amount']
        quotation_data['total'] = calculations['total']
        
        # Convert items back to dict format for JSON storage
        quotation_data['items'] = [item.model_dump() for item in items]
        
        return quotation_data
    
    async def create(
        self,
        db_conn: AsyncSession,
        model: QuotationModel,
        token_data: Optional[TokenData] = None
    ) -> QuotationModel:
        """
        Create a new quotation with auto-generated quotation number and calculated totals.
        """
        # Convert model to dict for processing
        model_dict = model.to_dict()
        
        # Generate quotation number if not provided
        if not model_dict.get('quotation_number'):
            model_dict['quotation_number'] = self._generate_quotation_number()
        
        # Calculate and update totals
        model_dict = self._calculate_and_update_totals(model_dict)
        
        # Create new model instance with updated data
        updated_model = QuotationModel(**model_dict)
        
        # Call parent create method
        return await super().create(db_conn, updated_model, token_data)
    
    async def update(
        self,
        db_conn: AsyncSession,
        id: str,
        update_data: dict,
        token_data: Optional[TokenData] = None
    ) -> QuotationModel:
        """
        Update a quotation and recalculate totals if items or percentages changed.
        """
        # Check if we need to recalculate
        needs_recalculation = any(
            key in update_data for key in [
                'items', 'discount_percentage', 'tax_percentage'
            ]
        )
        
        if needs_recalculation:
            # Get current quotation to merge data
            current_quotation = await self.get_by_id(db_conn, id, token_data)
            current_dict = current_quotation.to_dict()
            
            # Merge update data with current data
            merged_data = {**current_dict, **update_data}
            
            # Recalculate totals
            merged_data = self._calculate_and_update_totals(merged_data)
            
            # Update only the changed fields
            update_data = {
                k: v for k, v in merged_data.items()
                if k in update_data or k in [
                    'subtotal', 'discount_amount', 'tax_amount', 'total'
                ]
            }
        
        # Call parent update method
        return await super().update(db_conn, id, update_data, token_data)
