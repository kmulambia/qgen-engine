from engine.datasources.postgres_ds import PostgresDataSource
from engine.models import Base
from api.dependencies.logging import logger
from engine.utils.config_util import load_config

config = load_config()

POSTGRES_USER = config.require_variable("POSTGRES_USER")
POSTGRES_PASSWORD = config.require_variable("POSTGRES_PASSWORD")
POSTGRES_HOST = config.require_variable("POSTGRES_HOST")
POSTGRES_PORT = config.require_variable("POSTGRES_PORT", int)
POSTGRES_DB = config.require_variable("POSTGRES_DB")

db = PostgresDataSource(
    username=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    db_name=POSTGRES_DB,
    base=Base
)


async def get_db():
    """
    FastAPI dependency that provides a database session.
    Properly manages session lifecycle by committing and closing it after use.
    """
    session = None
    try:
        await db.connect()
        session = await db.get_session()
        yield session
        # Commit the transaction after successful execution
        await session.commit()
    except Exception as e:
        logger.error(f"Error connecting to PostgresSQL host:{POSTGRES_HOST} database: {POSTGRES_DB} database: {e}")
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()
