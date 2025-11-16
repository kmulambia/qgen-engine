import logging
import platform
import time
from typing import Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from api.dependencies.db import get_db
from api.dependencies.cache import get_cache
from engine.utils.config_util import load_config

logger = logging.getLogger(__name__)
router = APIRouter()
env = load_config()


@router.get("/ping")
async def ping() -> Dict[str, Any]:
    """Simple ping endpoint that returns basic application info."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": env.get_variable("NAME", "FastAPI Application"),
        "version": env.get_variable("VERSION", "0.0.0"),
        "environment": env.get_variable("ENVIRONMENT", "development")
    }


@router.get("/health")
async def health_check(
        db: AsyncSession = Depends(get_db),
        cache=Depends(get_cache)
) -> Dict[str, Any]:
    """
    Comprehensive health check that verifies all system components.
    Returns system health status and detailed component information.
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "system": {
                "status": "healthy",
                "python_version": platform.python_version(),
                "platform": platform.platform(),
            },
            "database": {
                "status": "unhealthy",
                "type": "postgresql",
                "details": None
            },
            "cache": {
                "status": "unhealthy",
                "type": "redis",
                "details": None
            }
        }
    }

    # Database Health Check
    try:
        db_start = time.time()
        db_result = await db.execute(text("SELECT version()"))
        db_version = db_result.fetchone()[0]  # No await on fetchone()
        health_status["components"]["database"].update({
            "status": "healthy",
            "details": {
                "version": db_version,
                "latency_ms": round((time.time() - db_start) * 1000, 2)
            }
        })
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["status"] = "degraded"

    # Cache Health Check
    try:
        cache_start = time.time()
        await cache.ping()
        cache_info = await cache.info()
        health_status["components"]["cache"].update({
            "status": "healthy",
            "details": {
                "version": cache_info.get("redis_version", "unknown"),
                "used_memory": cache_info.get("used_memory_human", "unknown"),
                "connected_clients": cache_info.get("connected_clients", "unknown"),
                "latency_ms": round((time.time() - cache_start) * 1000, 2)
            }
        })
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        health_status["components"]["cache"]["details"] = {"error": str(e)}  # type: ignore
        health_status["status"] = "degraded"

    # Overall response time
    health_status["response_time_ms"] = f"{round((time.time() - start_time) * 1000, 2)}"

    # Return appropriate status code if any component is unhealthy
    if health_status["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )

    return health_status


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness probe to verify if the application is ready to handle traffic."""
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness probe to verify if the application is running."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
