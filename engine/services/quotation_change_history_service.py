from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.quotation_change_history_model import QuotationChangeHistoryModel
from engine.repositories.quotation_change_history_repository import QuotationChangeHistoryRepository
from engine.services.base_service import BaseService
from engine.schemas.token_schemas import TokenData


class QuotationChangeHistoryService(BaseService[QuotationChangeHistoryModel]):
    """Service for managing quotation change history"""
    
    def __init__(self):
        super().__init__(QuotationChangeHistoryRepository())

    def _serialize_value(self, value: Any) -> Optional[Dict[str, Any]]:
        """
        Serialize a value to JSON-compatible format for storage.
        
        Args:
            value: The value to serialize
            
        Returns:
            Serialized value as dict or None
        """
        if value is None:
            return None
        
        # Handle common types that need special serialization
        if isinstance(value, (datetime,)):
            return {"_type": "datetime", "_value": value.isoformat()}
        elif isinstance(value, (date,)):
            return {"_type": "date", "_value": str(value)}
        elif hasattr(value, '__dict__'):
            # For objects, convert to dict
            try:
                return {"_type": "object", "_value": value.__dict__}
            except:
                return {"_type": "object", "_value": str(value)}
        elif isinstance(value, (list, dict)):
            # Already JSON-serializable
            return {"_type": "json", "_value": value}
        else:
            # Primitive types
            return {"_type": "primitive", "_value": value}

    async def track_change(
        self,
        db_conn: AsyncSession,
        quotation_id: UUID,
        change_type: str,
        field_name: str,
        from_value: Any = None,
        to_value: Any = None,
        user_id: Optional[UUID] = None,
        change_summary: Optional[Dict[str, Any]] = None
    ) -> QuotationChangeHistoryModel:
        """
        Record a single field change in the quotation change history.
        
        Args:
            db_conn: Database session
            quotation_id: UUID of the quotation
            change_type: Type of change (created, updated, approved, etc.)
            field_name: Name of the field that changed
            from_value: Previous value
            to_value: New value
            user_id: UUID of the user who made the change
            change_summary: Optional summary of all changes in this transaction
            
        Returns:
            Created change history record
        """
        change_record = QuotationChangeHistoryModel(
            quotation_id=quotation_id,
            user_id=user_id,
            change_type=change_type,
            field_name=field_name,
            from_value=self._serialize_value(from_value),
            to_value=self._serialize_value(to_value),
            change_summary=change_summary,
            created_at=datetime.now(timezone.utc)
        )
        
        return await self.repository.create(db_conn, change_record)

    async def track_changes(
        self,
        db_conn: AsyncSession,
        quotation_id: UUID,
        change_type: str,
        changes: List[Dict[str, Any]],
        user_id: Optional[UUID] = None
    ) -> List[QuotationChangeHistoryModel]:
        """
        Record multiple field changes in a single transaction.
        
        Args:
            db_conn: Database session
            quotation_id: UUID of the quotation
            change_type: Type of change (created, updated, etc.)
            changes: List of dicts with keys: field_name, from_value, to_value
            user_id: UUID of the user who made the change
            
        Returns:
            List of created change history records
        """
        records = []
        for change in changes:
            record = await self.track_change(
                db_conn=db_conn,
                quotation_id=quotation_id,
                change_type=change_type,
                field_name=change.get('field_name'),
                from_value=change.get('from_value'),
                to_value=change.get('to_value'),
                user_id=user_id
            )
            records.append(record)
        
        return records

    async def get_quotation_history(
        self,
        db_conn: AsyncSession,
        quotation_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[QuotationChangeHistoryModel]:
        """
        Get full change history for a quotation.
        
        Args:
            db_conn: Database session
            quotation_id: UUID of the quotation
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of change history records ordered by created_at descending
        """
        return await self.repository.get_by_quotation_id(
            session=db_conn,
            quotation_id=quotation_id,
            limit=limit,
            offset=offset,
            order_by_desc=True
        )

    async def get_field_history(
        self,
        db_conn: AsyncSession,
        quotation_id: UUID,
        field_name: str
    ) -> List[QuotationChangeHistoryModel]:
        """
        Get change history for a specific field of a quotation.
        
        Args:
            db_conn: Database session
            quotation_id: UUID of the quotation
            field_name: Name of the field to get history for
            
        Returns:
            List of change history records for the specified field
        """
        return await self.repository.get_by_field_name(
            session=db_conn,
            quotation_id=quotation_id,
            field_name=field_name
        )

