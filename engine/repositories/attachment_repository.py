from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.attachment_model import AttachmentModel
from engine.repositories.base_repository import BaseRepository


class AttachmentRepository(BaseRepository[AttachmentModel]):
    def __init__(self):
        super().__init__(AttachmentModel)

    async def get_by_application_id(
            self,
            db_conn: AsyncSession,
            application_id: UUID
    ) -> List[AttachmentModel]:
        """Get all attachments for a specific application"""
        query = select(self.model).where(
            self.model.application_id == application_id,
            self.model.is_deleted is False
        )
        result = await db_conn.execute(query)
        return list(result.scalars().all())

    async def get_by_workflow_stage(
            self,
            db_conn: AsyncSession,
            workflow_id: UUID,
            workflow_stage_id: UUID
    ) -> List[AttachmentModel]:
        """Get all attachments for a specific workflow stage"""
        query = select(self.model).where(
            self.model.workflow_id == workflow_id,
            self.model.workflow_stage_id == workflow_stage_id,
            self.model.is_deleted is False
        )
        result = await db_conn.execute(query)
        return list(result.scalars().all())
