from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from engine.models.user_model import UserModel
from engine.models.workspace_model import WorkspaceModel
from engine.models.role_model import RoleModel
from engine.models.audit_model import AuditModel
from typing import List, Dict, Any


# noinspection DuplicatedCode
class StatsService:
    def __init__(self):
        pass

    @staticmethod
    async def get_audit_activity_stats(
            db: AsyncSession,
            categories: Dict[str, List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get audit activity counts for the last 6 months by categories.
        
        Args:
            db: AsyncSession - The database session
            categories: Dict[str, List[str]] - Dictionary of category names and their associated actions
                       Default categories are logins, user activities, workspace activities, and role activities
        
        Returns:
            Dictionary containing datasets for each category with monthly counts
            :param db:
            :type categories:
        """
        try:
            # Calculate date ranges for last 6 months
            now = datetime.now()
            months = []
            datasets = []

            for i in range(6):
                # Calculate the start of the month i months ago
                year = now.year
                month = now.month - i
                if month <= 0:
                    year -= 1
                    month += 12
                month_start = datetime(year, month, 1)

                # Calculate the start of the next month (exclusive end date)
                next_month_start = (month_start + timedelta(days=32)).replace(day=1)

                months.insert(0, {
                    'start': month_start,
                    'end': next_month_start,
                    'label': month_start.strftime('%b')  # Month abbreviation
                })

            # Add dataset for all activities
            all_actions = [action for actions in categories.values() for action in actions]
            all_activities_data = []

            for month in months:
                query = select(func.count(AuditModel.id)).where(
                    and_(
                        AuditModel.created_at >= month['start'],
                        AuditModel.created_at < month['end'],
                        AuditModel.action.in_(all_actions)
                    )
                )
                result = await db.execute(query)
                count = result.scalar() or 0
                all_activities_data.append({
                    'label': month['label'],
                    'value': count
                })

            datasets.append({
                'label': 'All Activities',
                'data': all_activities_data
            })

            # Generate datasets for each category
            for category, actions in categories.items():
                category_data = []

                for month in months:
                    query = select(func.count(AuditModel.id)).where(
                        and_(
                            AuditModel.created_at >= month['start'],
                            AuditModel.created_at < month['end'],
                            AuditModel.action.in_(actions)
                        )
                    )
                    result = await db.execute(query)
                    count = result.scalar() or 0
                    category_data.append({
                        'label': month['label'],
                        'value': count
                    })

                datasets.append({
                    'label': category.replace('_', ' ').title(),
                    'data': category_data
                })

            return {
                'success': True,
                'data': {
                    'datasets': datasets
                }
            }
        except SQLAlchemyError as e:
            return {
                'success': False,
                'error': f"Database error occurred while fetching audit stats: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error occurred while fetching audit stats: {str(e)}"
            }

    @staticmethod
    async def get_user_monthly_stats(db: AsyncSession):
        try:
            # Get current time and first day of current and previous month
            now = datetime.now()
            current_month_start = datetime(now.year, now.month, 1)
            prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

            # Get total active users
            total_users_query = select(func.count(UserModel.id)).where(UserModel.is_deleted is False)
            total_result = await db.execute(total_users_query)
            total_users = total_result.scalar()

            # Get users created this month
            current_month_query = select(func.count(UserModel.id)).where(
                UserModel.created_at >= current_month_start,
                UserModel.is_deleted is False
            )
            current_month_result = await db.execute(current_month_query)
            current_month_users = current_month_result.scalar()

            # Get users created last month
            prev_month_query = select(func.count(UserModel.id)).where(
                UserModel.created_at >= prev_month_start,
                UserModel.created_at < current_month_start,
                UserModel.is_deleted is False
            )
            prev_month_result = await db.execute(prev_month_query)
            prev_month_users = prev_month_result.scalar()

            # Get users deleted in current month
            deleted_current_month_query = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.updated_at >= current_month_start,
                    UserModel.is_deleted is True
                )
            )
            deleted_current_month_result = await db.execute(deleted_current_month_query)
            deleted_current_month_users = deleted_current_month_result.scalar()

            # Calculate growth (new users minus deleted users)
            growth = current_month_users - deleted_current_month_users

            return {
                "success": True,
                "data": {
                    "total_users": total_users,
                    "current_month_users": current_month_users,
                    "previous_month_users": prev_month_users,
                    "growth": growth
                }
            }
        except SQLAlchemyError as e:
            return {
                "success": False,
                "error": f"Database error occurred while fetching user stats: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error occurred while fetching user stats: {str(e)}"
            }

    # noinspection DuplicatedCode
    @staticmethod
    async def get_workspace_monthly_stats(db: AsyncSession):
        try:
            now = datetime.now()
            current_month_start = datetime(now.year, now.month, 1)
            prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

            # Get total active workspaces
            total_workspaces_query = select(func.count(WorkspaceModel.id)).where(WorkspaceModel.is_deleted is False)
            total_result = await db.execute(total_workspaces_query)
            total_workspaces = total_result.scalar()

            # Get workspaces created this month
            current_month_query = select(func.count(WorkspaceModel.id)).where(
                WorkspaceModel.created_at >= current_month_start,
                WorkspaceModel.is_deleted is False
            )
            current_month_result = await db.execute(current_month_query)
            current_month_workspaces = current_month_result.scalar()

            # Get workspaces created last month
            prev_month_query = select(func.count(WorkspaceModel.id)).where(
                WorkspaceModel.created_at >= prev_month_start,
                WorkspaceModel.created_at < current_month_start,
                WorkspaceModel.is_deleted is False
            )
            prev_month_result = await db.execute(prev_month_query)
            prev_month_workspaces = prev_month_result.scalar()

            # Get workspaces deleted in current month
            deleted_current_month_query = select(func.count(WorkspaceModel.id)).where(
                and_(
                    WorkspaceModel.updated_at >= current_month_start,
                    WorkspaceModel.is_deleted is True
                )
            )
            deleted_current_month_result = await db.execute(deleted_current_month_query)
            deleted_current_month_workspaces = deleted_current_month_result.scalar()

            # Calculate growth
            growth = current_month_workspaces - deleted_current_month_workspaces

            return {
                "success": True,
                "data": {
                    "total_workspaces": total_workspaces,
                    "current_month_workspaces": current_month_workspaces,
                    "previous_month_workspaces": prev_month_workspaces,
                    "growth": growth
                }
            }
        except SQLAlchemyError as e:
            return {
                "success": False,
                "error": f"Database error occurred while fetching workspace stats: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error occurred while fetching workspace stats: {str(e)}"
            }

    # noinspection DuplicatedCode
    @staticmethod
    async def get_role_monthly_stats(db: AsyncSession):
        try:
            now = datetime.now()
            current_month_start = datetime(now.year, now.month, 1)
            prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

            # Get total active roles
            total_roles_query = select(func.count(RoleModel.id)).where(RoleModel.is_deleted is False)
            total_result = await db.execute(total_roles_query)
            total_roles = total_result.scalar()

            # Get roles created this month
            current_month_query = select(func.count(RoleModel.id)).where(
                RoleModel.created_at >= current_month_start,
                RoleModel.is_deleted is False
            )
            current_month_result = await db.execute(current_month_query)
            current_month_roles = current_month_result.scalar()

            # Get roles created last month
            prev_month_query = select(func.count(RoleModel.id)).where(
                RoleModel.created_at >= prev_month_start,
                RoleModel.created_at < current_month_start,
                RoleModel.is_deleted is False
            )
            prev_month_result = await db.execute(prev_month_query)
            prev_month_roles = prev_month_result.scalar()

            # Get roles deleted in current month
            deleted_current_month_query = select(func.count(RoleModel.id)).where(
                and_(
                    RoleModel.updated_at >= current_month_start,
                    RoleModel.is_deleted is True
                )
            )
            deleted_current_month_result = await db.execute(deleted_current_month_query)
            deleted_current_month_roles = deleted_current_month_result.scalar()

            # Calculate growth
            growth = current_month_roles - deleted_current_month_roles

            return {
                "success": True,
                "data": {
                    "total_roles": total_roles,
                    "current_month_roles": current_month_roles,
                    "previous_month_roles": prev_month_roles,
                    "growth": growth
                }
            }
        except SQLAlchemyError as e:
            return {
                "success": False,
                "error": f"Database error occurred while fetching role stats: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error occurred while fetching role stats: {str(e)}"
            }
