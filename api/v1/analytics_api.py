from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json
from typing import Dict, Any, Optional
from api.dependencies.db import get_db
from api.dependencies.ratelimiter import rate_limit
from engine.utils.config_util import load_config
from engine.services.analytics.stats_service import StatsService

logger = logging.getLogger(__name__)
router = APIRouter()

config = load_config()
MODE = config.get_variable("MODE", "development")
stats_service = StatsService()


@router.get("/stats/monthly/users")
@rate_limit()
async def get_user_monthly_stats(
        db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get monthly statistics for users including total count, new users this month,
    new users last month, and growth rate.
    """
    try:
        result = await stats_service.get_user_monthly_stats(db)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return result["data"]
    except Exception as e:
        error_details = str(e) if MODE == "development" else "An error occurred while fetching the stats."
        logger.error(f"Failed to get user monthly stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user monthly stats: {error_details}"
        )


@router.get("/stats/monthly/workspaces")
@rate_limit()
async def get_workspace_monthly_stats(
        db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get monthly statistics for workspaces including total count, new workspaces this month,
    new workspaces last month, and growth rate.
    """
    try:
        result = await stats_service.get_workspace_monthly_stats(db)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return result["data"]

    except Exception as e:
        error_details = str(e) if MODE == "development" else "An error occurred while fetching the stats."
        logger.error(f"Failed to get workspace monthly stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace monthly stats: {error_details}"
        )


@router.get("/stats/monthly/roles")
@rate_limit()
async def get_role_monthly_stats(
        db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get monthly statistics for roles including total count, new roles this month,
    new roles last month, and growth rate.
    """
    try:
        result = await stats_service.get_role_monthly_stats(db)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return result["data"]

    except Exception as e:
        error_details = str(e) if MODE == "development" else "An error occurred while fetching the stats."
        logger.error(f"Failed to get role monthly stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get role monthly stats: {error_details}"
        )


@router.get("/stats/audit-activities")
@rate_limit()
async def get_audit_activity_stats(
        categories_json: Optional[str] = Query(
            None,
            description="Optional JSON string of category mappings. Format: {'category_name': ['action1', 'action2']}"
        ),
        db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get audit activity statistics for the last 6 months grouped by categories.
    
    Args:
        categories_json: Optional JSON string mapping category names to lists of audit actions.
                        Example: {"logins": ["login", "logout"]}
                        If not provided, default categories will be used:
                        - logins: login/logout activities
                        - user_activities: user-related actions
                        - workspace_activities: workspace-related actions
                        - role_activities: role-related actions
        db: Database session dependency for executing queries
    
    Returns:
        Dictionary containing datasets for each category with monthly activity counts
    """
    try:
        categories = None
        if categories_json:
            try:
                categories = json.loads(categories_json)
                if not isinstance(categories, dict):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Categories must be a JSON object mapping category names to action lists"
                    )
                for key, value in categories.items():
                    if not isinstance(value, list):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Category '{key}' must map to a list of actions"
                        )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format for categories"
                )

        result = await stats_service.get_audit_activity_stats(db, categories)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return result["data"]

    except HTTPException:
        raise
    except Exception as e:
        error_details = str(e) if MODE == "development" else "An error occurred while fetching the stats."
        logger.error(f"Failed to get audit activity stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit activity stats: {error_details}"
        )
