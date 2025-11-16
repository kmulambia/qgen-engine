from engine.datasources.postgres_ds import PostgresDataSource
from engine.models import Base
from mailer.dependencies.logger import logger
from engine.utils.config_util import load_config

config = load_config()

POSTGRES_USER = config.require_variable("POSTGRES_USER")
POSTGRES_PASSWORD = config.require_variable("POSTGRES_PASSWORD")
POSTGRES_HOST = config.require_variable("POSTGRES_HOST")
POSTGRES_PORT = config.require_variable("POSTGRES_PORT", int)
POSTGRES_DB = config.require_variable("POSTGRES_DB")


async def get_db() -> PostgresDataSource:
    """Get PostgreSQL database session."""

    try:
        postgres_ds = PostgresDataSource(
            username=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            db_name=POSTGRES_DB,
            base=Base
        )

        return postgres_ds
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL host:{POSTGRES_HOST} database: {POSTGRES_DB} database: {e}")
        raise
