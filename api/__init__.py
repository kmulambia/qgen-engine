"""
 * Framework - Backend and Services
 * MIT License
 * Copyright (c) 2024 Umodzi Source
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi.openapi.utils import get_openapi
import uvicorn
from api.dependencies.db import get_db, db as db
from api.dependencies.cache import get_cache, cache as cache
from api.v1.router import router as v1_router
from api.dependencies.ratelimiter import RateLimitMiddleware
from api.dependencies.cors_override import CORSEOverrideMiddleware
from api.dependencies.logging import logger
from engine.utils.config_util import load_config

config = load_config()

# SSL context configuration (commented out if not using SSL)
# ssl_context = SSLContext(PROTOCOL_TLS_SERVER)
# ssl_context.load_cert_chain(certfile="path/to/cert", keyfile="path/to/key")

RATE_LIMIT_REQUESTS = config.require_variable("RATE_LIMIT_REQUESTS", int)
RATE_LIMIT_WINDOW = config.require_variable("RATE_LIMIT_WINDOW", int)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:  # noqa
    """Manages the startup and shutdown of database connections."""
    logger.info("Starting application and connecting to databases.")
    try:
        # Initialize database connection (but don't get a session yet)
        await db.connect()
        app.state.db = db  # noqa
        
        # Initialize Redis cache
        redis = await get_cache()
        app.state.cache = redis  # noqa
        
        logger.info("Database and cache connections established successfully.")
    except Exception as e:
        logger.error(f"Error during database connection: {e}")
        raise RuntimeError("Failed to start application due to database connection issues") from e

    yield

    logger.info("Shutting down application and disconnecting databases.")
    try:
        await db.close()
        await cache.disconnect()
        logger.info("Database and cache connections closed successfully.")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title=config.require_variable("NAME"),
    description=config.require_variable("DESCRIPTION"),
    version=config.require_variable("VERSION"),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Remove HTTPS redirect if not using SSL
# app.add_middleware(HTTPSRedirectMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=config.get_variable("CORS_ORIGINS", "*").split(","),  # noqa
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORS override middleware - runs after CORS middleware to override headers for file endpoints
# This ensures specific origin (not wildcard) is used when credentials mode is enabled
app.add_middleware(CORSEOverrideMiddleware)  # noqa

app.add_middleware(RateLimitMiddleware)  # noqa


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=config.require_variable("NAME"),
        description=config.require_variable("DESCRIPTION"),
        version=config.require_variable("VERSION"),
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# API routes
app.include_router(v1_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=config.require_variable("HOST"),
        port=config.require_variable("PORT", int),
        reload=True,
        # ssl_keyfile="path/to/key",  # Uncomment and set if using SSL
        # ssl_certfile="path/to/cert"  # Uncomment and set if using SSL
    )
