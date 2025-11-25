from uuid import UUID
from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.quotation_change_history_model import QuotationChangeHistoryModel
from engine.repositories.base_repository import BaseRepository


class QuotationChangeHistoryRepository(BaseRepository[QuotationChangeHistoryModel]):
    def __init__(self):
        super().__init__(QuotationChangeHistoryModel)

    async def get_by_quotation_id(
        self,
        session: AsyncSession,
        quotation_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by_desc: bool = True
    ) -> List[QuotationChangeHistoryModel]:
        """
        Get all change history records for a specific quotation.
        
        Args:
            session: Database session
            quotation_id: UUID of the quotation
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by_desc: If True, order by created_at descending (newest first)
            
        Returns:
            List of change history records
        """
        stmt = (
            select(QuotationChangeHistoryModel)
            .where(
                and_(
                    QuotationChangeHistoryModel.quotation_id == quotation_id,
                    QuotationChangeHistoryModel.is_deleted.is_(False)
                )
            )
        )
        
        if order_by_desc:
            stmt = stmt.order_by(desc(QuotationChangeHistoryModel.created_at))
        else:
            stmt = stmt.order_by(QuotationChangeHistoryModel.created_at)
        
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_changes(
        self,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> List[QuotationChangeHistoryModel]:
        """
        Get recent changes across all quotations with pagination.
        
        Args:
            session: Database session
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of recent change history records
        """
        stmt = (
            select(QuotationChangeHistoryModel)
            .where(QuotationChangeHistoryModel.is_deleted.is_(False))
            .order_by(desc(QuotationChangeHistoryModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_field_name(
        self,
        session: AsyncSession,
        quotation_id: UUID,
        field_name: str
    ) -> List[QuotationChangeHistoryModel]:
        """
        Get change history for a specific field of a quotation.
        
        Args:
            session: Database session
            quotation_id: UUID of the quotation
            field_name: Name of the field to get history for
            
        Returns:
            List of change history records for the specified field
        """
        stmt = (
            select(QuotationChangeHistoryModel)
            .where(
                and_(
                    QuotationChangeHistoryModel.quotation_id == quotation_id,
                    QuotationChangeHistoryModel.field_name == field_name,
                    QuotationChangeHistoryModel.is_deleted.is_(False)
                )
            )
            .order_by(desc(QuotationChangeHistoryModel.created_at))
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())

