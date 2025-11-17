from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from engine.models.layout_model import LayoutModel
from engine.repositories.layout_repository import LayoutRepository
from engine.services.base_service import BaseService
from engine.schemas.token_schemas import TokenData


class LayoutService(BaseService[LayoutModel]):
    """Service for layout business logic"""

    def __init__(self):
        super().__init__(LayoutRepository())

    async def set_default_layout(
        self,
        db_conn: AsyncSession,
        layout_id: UUID,
        token_data: Optional[TokenData] = None
    ) -> LayoutModel:
        """
        Set a layout as the default layout.
        Ensures only one layout can be default at a time.
        
        Args:
            db_conn: Database session
            layout_id: UUID of the layout to set as default
            token_data: Optional token data for auditing
            
        Returns:
            The updated layout model
        """
        try:
            # First, unset any existing default layouts
            await db_conn.execute(
                update(LayoutModel)
                .where(and_(
                    LayoutModel.is_default.is_(True),
                    LayoutModel.is_deleted.is_(False)
                ))
                .values(is_default=False)
            )
            
            # Set the new default layout
            result = await db_conn.execute(
                update(LayoutModel)
                .where(and_(
                    LayoutModel.id == layout_id,
                    LayoutModel.is_deleted.is_(False)
                ))
                .values(is_default=True)
                .returning(LayoutModel)
            )
            
            await db_conn.commit()
            layout = result.scalar_one_or_none()
            
            if layout and token_data:
                await self.audit(
                    db_conn,
                    f"{self.service_name}.set_default",
                    {
                        "id": str(token_data.user_id),
                        "first_name": token_data.first_name,
                        "last_name": token_data.last_name,
                        "email": token_data.email
                    },
                    entity_metadata={
                        "layout_id": str(layout_id),
                        "layout_name": layout.name
                    }
                )
            
            return layout
            
        except Exception as e:
            await db_conn.rollback()
            raise e

    async def get_default_layout(
        self,
        db_conn: AsyncSession
    ) -> Optional[LayoutModel]:
        """
        Get the current default layout.
        
        Args:
            db_conn: Database session
            
        Returns:
            The default layout model if one exists, None otherwise
        """
        try:
            result = await db_conn.execute(
                select(LayoutModel)
                .where(and_(
                    LayoutModel.is_default.is_(True),
                    LayoutModel.is_deleted.is_(False)
                ))
            )
            return result.scalar_one_or_none()
            
        except Exception:
            raise

    async def update_logo(
        self,
        db_conn: AsyncSession,
        layout_id: UUID,
        logo_file_id: UUID,
        token_data: Optional[TokenData] = None
    ) -> LayoutModel:
        """
        Update the logo file for a layout.
        
        Args:
            db_conn: Database session
            layout_id: UUID of the layout to update
            logo_file_id: UUID of the new logo file
            token_data: Optional token data for auditing
            
        Returns:
            The updated layout model
        """
        try:
            result = await db_conn.execute(
                update(LayoutModel)
                .where(and_(
                    LayoutModel.id == layout_id,
                    LayoutModel.is_deleted.is_(False)
                ))
                .values(logo_file_id=logo_file_id)
                .returning(LayoutModel)
            )
            
            await db_conn.commit()
            layout = result.scalar_one_or_none()
            
            if layout and token_data:
                await self.audit(
                    db_conn,
                    f"{self.service_name}.update_logo",
                    {
                        "id": str(token_data.user_id),
                        "first_name": token_data.first_name,
                        "last_name": token_data.last_name,
                        "email": token_data.email
                    },
                    entity_metadata={
                        "layout_id": str(layout_id),
                        "logo_file_id": str(logo_file_id)
                    }
                )
            
            return layout
            
        except Exception as e:
            await db_conn.rollback()
            raise e

    async def remove_logo(
        self,
        db_conn: AsyncSession,
        layout_id: UUID,
        token_data: Optional[TokenData] = None
    ) -> LayoutModel:
        """
        Remove the logo from a layout.
        
        Args:
            db_conn: Database session
            layout_id: UUID of the layout to update
            token_data: Optional token data for auditing
            
        Returns:
            The updated layout model
        """
        try:
            result = await db_conn.execute(
                update(LayoutModel)
                .where(and_(
                    LayoutModel.id == layout_id,
                    LayoutModel.is_deleted.is_(False)
                ))
                .values(logo_file_id=None)
                .returning(LayoutModel)
            )
            
            await db_conn.commit()
            layout = result.scalar_one_or_none()
            
            if layout and token_data:
                await self.audit(
                    db_conn,
                    f"{self.service_name}.remove_logo",
                    {
                        "id": str(token_data.user_id),
                        "first_name": token_data.first_name,
                        "last_name": token_data.last_name,
                        "email": token_data.email
                    },
                    entity_metadata={
                        "layout_id": str(layout_id)
                    }
                )
            
            return layout
            
        except Exception as e:
            await db_conn.rollback()
            raise e
