from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.quotation_model import QuotationModel
from engine.repositories.quotation_repository import QuotationRepository
from engine.services.base_service import BaseService
from engine.services.quotation_change_history_service import QuotationChangeHistoryService
from engine.schemas.quotation_schemas import calculate_quotation_totals, QuotationItemSchema
from engine.schemas.token_schemas import TokenData
from engine.utils.jwt_util import JWTUtil
import json


class QuotationService(BaseService[QuotationModel]):
    def __init__(self):
        super().__init__(QuotationRepository())
        self.change_history_service = QuotationChangeHistoryService()
    
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
        # Use mode='json' to serialize Decimals as floats
        quotation_data['items'] = [item.model_dump(mode='json') for item in items]
        
        return quotation_data
    
    def _compare_values(self, old_value: Any, new_value: Any) -> bool:
        """
        Compare two values for equality, handling special types.
        
        Args:
            old_value: Previous value
            new_value: New value
            
        Returns:
            True if values are equal, False otherwise
        """
        # Handle None cases
        if old_value is None and new_value is None:
            return True
        if old_value is None or new_value is None:
            return False
        
        # Handle Decimal comparison
        if isinstance(old_value, Decimal) and isinstance(new_value, Decimal):
            return old_value == new_value
        if isinstance(old_value, Decimal):
            return old_value == Decimal(str(new_value))
        if isinstance(new_value, Decimal):
            return Decimal(str(old_value)) == new_value
        
        # Handle list/dict comparison (for items array)
        if isinstance(old_value, (list, dict)) and isinstance(new_value, (list, dict)):
            return json.dumps(old_value, sort_keys=True, default=str) == json.dumps(new_value, sort_keys=True, default=str)
        
        # Default comparison
        return old_value == new_value
    
    def _detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect all field changes between old and new quotation data.
        
        Args:
            old_data: Dictionary of old quotation data
            new_data: Dictionary of new quotation data
            
        Returns:
            List of change dictionaries with field_name, from_value, to_value
        """
        changes = []
        
        # Fields to track (exclude internal/system fields)
        fields_to_track = [
            'title', 'description', 'client_id', 'layout_id', 'quotation_date',
            'valid_until', 'items', 'currency', 'discount_percentage', 'tax_percentage',
            'notes', 'terms_conditions', 'quotation_status', 'quotation_number'
        ]
        
        for field in fields_to_track:
            old_val = old_data.get(field)
            new_val = new_data.get(field)
            
            # Skip if field not in new data (not being updated)
            if field not in new_data:
                continue
            
            # Compare values
            if not self._compare_values(old_val, new_val):
                changes.append({
                    'field_name': field,
                    'from_value': old_val,
                    'to_value': new_val
                })
        
        return changes
    
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
        created_quotation = await super().create(db_conn, updated_model, token_data)
        
        # Track creation in change history
        if token_data:
            user_id = token_data.user_id
            # Track all initial fields as "created" change type
            for field_name, field_value in model_dict.items():
                if field_name not in ['id', 'created_at', 'updated_at', 'is_deleted', 'status']:
                    try:
                        await self.change_history_service.track_change(
                            db_conn=db_conn,
                            quotation_id=created_quotation.id,
                            change_type="created",
                            field_name=field_name,
                            from_value=None,
                            to_value=field_value,
                            user_id=user_id
                        )
                    except Exception as e:
                        # Log error but don't fail the creation
                        print(f"Failed to track change history for field {field_name}: {e}")
        
        return created_quotation
    
    async def update(
        self,
        db_conn: AsyncSession,
        uid: UUID,
        data: QuotationModel,
        token_data: Optional[TokenData] = None
    ) -> Optional[QuotationModel]:
        """
        Update a quotation and recalculate totals if items or percentages changed.
        """
        # Convert model to dict for processing
        update_data = data.to_dict()
        
        # Remove None values and internal attributes
        update_data = {
            k: v for k, v in update_data.items()
            if v is not None and not k.startswith('_')
        }
        
        # Check if we need to recalculate
        needs_recalculation = any(
            key in update_data for key in [
                'items', 'discount_percentage', 'tax_percentage'
            ]
        )
        
        if needs_recalculation:
            # Get current quotation to merge data
            current_quotation = await self.get_by_id(db_conn, uid)
            if not current_quotation:
                return None
            current_dict = current_quotation.to_dict()
            
            # Merge update data with current data
            merged_data = {**current_dict, **update_data}
            
            # Recalculate totals
            merged_data = self._calculate_and_update_totals(merged_data)
            
            # Update only the changed fields plus calculated fields
            # Filter out None values and internal attributes
            final_update_data = {
                k: v for k, v in merged_data.items()
                if (k in update_data or k in ['subtotal', 'discount_amount', 'tax_amount', 'total']) 
                and v is not None 
                and not k.startswith('_')
            }
            
            # Create a new model instance with updated data for the parent update
            updated_model = QuotationModel(**final_update_data)
        else:
            # No recalculation needed, use the original data
            updated_model = data
        
        # Get current quotation for change tracking
        current_quotation = await self.get_by_id(db_conn, uid)
        if not current_quotation:
            return None
        
        current_dict = current_quotation.to_dict()
        new_dict = updated_model.to_dict()
        
        # Detect changes
        changes = self._detect_changes(current_dict, new_dict)
        
        # Call parent update method
        updated_quotation = await super().update(db_conn, uid, updated_model, token_data)
        
        # Track changes in history
        if updated_quotation and token_data and changes:
            user_id = token_data.user_id
            try:
                await self.change_history_service.track_changes(
                    db_conn=db_conn,
                    quotation_id=uid,
                    change_type="updated",
                    changes=changes,
                    user_id=user_id
                )
            except Exception as e:
                # Log error but don't fail the update
                print(f"Failed to track change history: {e}")
        
        return updated_quotation
    
    def _get_client_email(self, client) -> Optional[str]:
        """
        Get client email with fallback logic.
        Prefers contact_person_email, falls back to email.
        
        Args:
            client: ClientModel instance
            
        Returns:
            Email address or None if neither is available
        """
        if client.contact_person_email:
            return client.contact_person_email
        return client.email if client.email else None
    
    def _generate_access_token(self, quotation_id: UUID) -> Tuple[str, datetime]:
        """
        Generate a secure JWT token for public quotation access.
        
        Args:
            quotation_id: UUID of the quotation
            
        Returns:
            Tuple of (token_string, expiration_datetime)
        """
        token_data = {
            "quotation_id": str(quotation_id),
            "type": "quotation_access"
        }
        # Token expires in 30 days
        expires_delta = timedelta(days=30)
        token, expires_at = JWTUtil.encode_token(token_data, expires_delta)
        return token, expires_at
    
    async def approve_quotation(
        self,
        db_conn: AsyncSession,
        quotation_id: str,
        token_data: Optional[TokenData] = None
    ) -> QuotationModel:
        """
        Approve a quotation (status set to approved).
        
        Args:
            db_conn: Database connection
            quotation_id: UUID of the quotation
            token_data: Optional token data for auditing
            
        Returns:
            Updated QuotationModel with approved status and token
            
        Raises:
            Exception: If quotation not found, invalid status, or no client email
        """
        # Get quotation with client relationship
        quotation = await self.get_by_id(db_conn, UUID(quotation_id))
        if not quotation:
            raise Exception("quotation_not_found")
        
        # Validate quotation status
        if quotation.quotation_status not in ["draft", "approved"]:
            raise Exception("invalid_quotation_status")
        
        # Get client email
        if not quotation.client:
            raise Exception("client_not_found")
        
        client_email = self._get_client_email(quotation.client)
        if not client_email:
            raise Exception("client_email_not_found")
        
        # Generate access token
        access_token, token_expires_at = self._generate_access_token(quotation.id)
        
        # Update quotation - create model instance with update data
        # Get current quotation data and merge with updates
        current_dict = quotation.to_dict()
        current_dict.update({
            "quotation_status": "approved",
            "sent_at": datetime.now(timezone.utc),
            "access_token": access_token,
            "token_expires_at": token_expires_at
        })
        update_model = QuotationModel(**current_dict)
        
        # Track status change before update
        old_status = quotation.quotation_status
        if token_data and old_status != "approved":
            try:
                await self.change_history_service.track_change(
                    db_conn=db_conn,
                    quotation_id=quotation.id,
                    change_type="approved",
                    field_name="quotation_status",
                    from_value=old_status,
                    to_value="approved",
                    user_id=token_data.user_id
                )
            except Exception as e:
                print(f"Failed to track approval in change history: {e}")
        
        updated_quotation = await self.update(db_conn, quotation.id, update_model, token_data)
        
        # Reload with relationships
        return await self.get_by_id(db_conn, UUID(quotation_id))
    
    async def resend_quotation(
        self,
        db_conn: AsyncSession,
        quotation_id: str,
        token_data: Optional[TokenData] = None
    ) -> QuotationModel:
        """
        Resend a quotation to the client.
        Regenerates token if expired or missing, updates sent_at timestamp.
        
        Args:
            db_conn: Database connection
            quotation_id: UUID of the quotation
            token_data: Optional token data for auditing
            
        Returns:
            Updated QuotationModel
            
        Raises:
            Exception: If quotation not found or no client email
        """
        # Get quotation with client relationship
        quotation = await self.get_by_id(db_conn, UUID(quotation_id))
        if not quotation:
            raise Exception("quotation_not_found")
        
        # Get client email
        if not quotation.client:
            raise Exception("client_not_found")
        
        client_email = self._get_client_email(quotation.client)
        if not client_email:
            raise Exception("client_email_not_found")
        
        # Check if token needs regeneration
        needs_new_token = False
        if not quotation.access_token or not quotation.token_expires_at:
            needs_new_token = True
        elif quotation.token_expires_at < datetime.now(timezone.utc):
            needs_new_token = True
        
        # Get current quotation data and merge with updates
        current_dict = quotation.to_dict()
        current_dict.update({
            "sent_at": datetime.now(timezone.utc)
        })
        
        if needs_new_token:
            access_token, token_expires_at = self._generate_access_token(quotation.id)
            current_dict["access_token"] = access_token
            current_dict["token_expires_at"] = token_expires_at
        
        # Update quotation (status remains unchanged if already sent)
        update_model = QuotationModel(**current_dict)
        
        # Track resend action
        if token_data:
            try:
                changes_to_track = []
                if needs_new_token:
                    changes_to_track.append({
                        'field_name': 'access_token',
                        'from_value': quotation.access_token,
                        'to_value': access_token
                    })
                changes_to_track.append({
                    'field_name': 'sent_at',
                    'from_value': quotation.sent_at,
                    'to_value': datetime.now(timezone.utc)
                })
                
                await self.change_history_service.track_changes(
                    db_conn=db_conn,
                    quotation_id=quotation.id,
                    change_type="resend",
                    changes=changes_to_track,
                    user_id=token_data.user_id
                )
            except Exception as e:
                print(f"Failed to track resend in change history: {e}")
        
        updated_quotation = await self.update(db_conn, quotation.id, update_model, token_data)
        
        # Reload with relationships
        return await self.get_by_id(db_conn, UUID(quotation_id))
