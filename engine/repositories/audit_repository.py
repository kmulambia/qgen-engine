from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models import AuditModel
from engine.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditModel]):
    def __init__(self):
        super().__init__(AuditModel)

    async def get_last_action_by_user(
        self,
        user_id: UUID,
        action: str,
        session: AsyncSession,
        status: Optional[str] = "success"
    ) -> Optional[AuditModel]:
        """
        Get the most recent audit log for a specific user and action.
        Optimized single query with proper indexing.
        """
        stmt = (
            select(AuditModel)
            .where(
                and_(
                    AuditModel.user_id == user_id,
                    AuditModel.action == action,
                    AuditModel.status == status if status else True
                )
            )
            .order_by(desc(AuditModel.created_at))
            .limit(1)
        )
        
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_security_summary(
        self,
        user_id: UUID,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get comprehensive security summary for a user in a single optimized query.
        Returns last login, last password reset, and activity counts.
        """
        # Get last successful login
        last_login_stmt = (
            select(AuditModel)
            .where(
                and_(
                    AuditModel.user_id == user_id,
                    AuditModel.action == "user.login",
                    AuditModel.status == "success"
                )
            )
            .order_by(desc(AuditModel.created_at))
            .limit(1)
        )
        last_login_result = await session.execute(last_login_stmt)
        last_login = last_login_result.scalar_one_or_none()

        # Get last password reset
        # For password changes, we need to check both:
        # 1. user_id (for self password changes)
        # 2. entity_metadata.id (for admin changing another user's password)
        from sqlalchemy import or_, cast, String
        from sqlalchemy.dialects.postgresql import JSONB
        
        last_password_reset_stmt = (
            select(AuditModel)
            .where(
                and_(
                    AuditModel.action.in_(["user.password_reset", "user.password_change", "user.password_change_by_admin"]),
                    or_(
                        AuditModel.user_id == user_id,
                        cast(AuditModel.entity_metadata['id'], String) == str(user_id)
                    ),
                    AuditModel.status == "success"
                )
            )
            .order_by(desc(AuditModel.created_at))
            .limit(1)
        )
        last_password_reset_result = await session.execute(last_password_reset_stmt)
        last_password_reset = last_password_reset_result.scalar_one_or_none()

        # Get failed login attempts count (last 30 days)
        # Failed logins may have NULL user_id, so we check entity_metadata.email
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # First, get the user's email to check in entity_metadata
        user_email_stmt = select(AuditModel.user_metadata['email']).where(AuditModel.user_id == user_id).limit(1)
        user_email_result = await session.execute(user_email_stmt)
        user_email_row = user_email_result.first()
        
        if user_email_row and user_email_row[0]:
            user_email = user_email_row[0]
            failed_login_count_stmt = (
                select(func.count(AuditModel.id))
                .where(
                    and_(
                        AuditModel.action == "user.login",
                        AuditModel.status == "failed",
                        AuditModel.created_at >= thirty_days_ago,
                        or_(
                            AuditModel.user_id == user_id,
                            cast(AuditModel.entity_metadata['email'], String) == user_email
                        )
                    )
                )
            )
        else:
            # Fallback to just user_id if we can't get email
            failed_login_count_stmt = (
                select(func.count(AuditModel.id))
                .where(
                    and_(
                        AuditModel.user_id == user_id,
                        AuditModel.action == "user.login",
                        AuditModel.status == "failed",
                        AuditModel.created_at >= thirty_days_ago
                    )
                )
            )
        
        failed_login_count_result = await session.execute(failed_login_count_stmt)
        failed_login_count = failed_login_count_result.scalar() or 0

        return {
            "last_login": last_login,
            "last_password_reset": last_password_reset,
            "failed_login_count": failed_login_count
        }

    async def get_user_activity_stats(
        self,
        user_id: UUID,
        session: AsyncSession,
        days: int = 30
    ) -> Dict[str, int]:
        """
        Get user activity statistics for the specified time period.
        Optimized to reduce multiple queries.
        """
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        # Count by action type in a single query
        stmt = (
            select(
                AuditModel.action,
                func.count(AuditModel.id).label("count")
            )
            .where(
                and_(
                    AuditModel.user_id == user_id,
                    AuditModel.created_at >= start_date
                )
            )
            .group_by(AuditModel.action)
        )

        result = await session.execute(stmt)
        stats = {row.action: row.count for row in result}

        return stats

