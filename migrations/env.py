"""
 * Amphibia Framework - Backend and Services
 * MIT License
 * Copyright (c) 2024 Umodzi Source
 * https://amphibia.umodzisource.com
"""
from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv
from alembic import context
from engine.models import Base

load_dotenv()

config = context.config

try:
    db_uri = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{int(os.getenv('POSTGRES_PORT'))}/{os.getenv('POSTGRES_DB')}"
    )

    config.set_main_option("sqlalchemy.url", db_uri)

except (TypeError, ValueError):
    raise Exception("PostgreSQL environment variables are not properly set or invalid.")

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set up target metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
