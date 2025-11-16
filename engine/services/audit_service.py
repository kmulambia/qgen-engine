from uuid import UUID
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.audit_model import AuditModel
from engine.repositories.audit_repository import AuditRepository
from engine.services.base_service import BaseService


class AuditService(BaseService[AuditModel]):
    def __init__(self):
        super().__init__(AuditRepository())

    async def get_user_security_summary(
        self,
        user_id: UUID,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get comprehensive security summary for a user.
        Uses optimized repository method to minimize database queries.
        """
        return await self.repository.get_user_security_summary(user_id, session)

    async def get_last_action_by_user(
        self,
        user_id: UUID,
        action: str,
        session: AsyncSession,
        status: str = "success"
    ) -> AuditModel | None:
        """
        Get the most recent audit log for a specific user and action.
        """
        return await self.repository.get_last_action_by_user(
            user_id, action, session, status
        )

    async def get_user_activity_stats(
        self,
        user_id: UUID,
        session: AsyncSession,
        days: int = 30
    ) -> Dict[str, int]:
        """
        Get user activity statistics for the specified time period.
        """
        return await self.repository.get_user_activity_stats(user_id, session, days)

