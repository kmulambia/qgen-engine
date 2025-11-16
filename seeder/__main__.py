"""
 * Framework - Backend and Services
 * MIT License
 * Copyright (c) 2024 Umodzi Source
"""
import asyncio
from contextlib import asynccontextmanager
from engine.models.base_model import Base
from engine.utils.config_util import load_config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from seeder.dependencies.logging import logger
from seeder.dependencies.db import get_db

# System seeders
from seeder.permission_seeder import seeder as permission_seeder
from seeder.role_seeder import seeder as role_seeder
from seeder.user_seeder import seeder as user_seeder

# Workspace seeders
from seeder.workspace_type_seeder import seeder as workspace_type_seeder
from seeder.workspace_seeder import seeder as workspace_seeder


config = load_config()

if not config:
    raise ValueError("Environment configuration not found")


@asynccontextmanager
async def get_db_connection():
    """
    Context manager for database connection
    """
    connection = await get_db()
    try:
        yield connection
    finally:
        await connection.close()


async def drop_all_tables(session: AsyncSession):
    """Drop all existing tables from the database."""
    try:
        await session.run_sync(lambda sync_session: Base.metadata.drop_all(bind=sync_session.get_bind()))
        logger.info("All tables dropped successfully")
    except Exception as error:
        logger.error(f"Error dropping tables: {str(error)}", exc_info=True)
        raise


async def truncate_all_tables(session: AsyncSession):
    """Truncate all tables in the database."""
    try:
        table_names = Base.metadata.tables.keys()
        for table_name in table_names:
            formatted_query = f'TRUNCATE TABLE "{table_name}" CASCADE'
            await session.execute(text(formatted_query))
        logger.info("All tables truncated successfully")
    except Exception as error:
        logger.error(f"Error truncating tables: {str(error)}", exc_info=True)
        raise


async def create_tables(session: AsyncSession):
    """Create all database tables."""
    try:
        await session.run_sync(lambda sync_session: Base.metadata.create_all(bind=sync_session.get_bind()))
        logger.info("All tables created successfully")
    except Exception as error:
        logger.error(f"Error creating tables: {str(error)}", exc_info=True)
        raise


async def run_seeders(session: AsyncSession):
    """Run all seeders organized by category."""
    # Define seeder groups
    system_seeders = [
        (permission_seeder, "permission seeding"),
        (role_seeder, "role seeding"),
    ]

    workspace_seeders = [
        (workspace_type_seeder, "workspace type seeding"),
        (workspace_seeder, "workspace seeding"),
    ]

    seeder_groups = [
        ("System Data", system_seeders),
        ("Workspace Data", workspace_seeders),
    ]

    for group_name, seeders in seeder_groups:
        logger.info(f"Running {group_name} seeders...")
        for seeder, name in seeders:
            try:
                await seeder(session)
                logger.info(f"Successfully completed {name}")
            except Exception as error:
                logger.error(f"Error during {name}: {str(error)}", exc_info=True)
                raise


async def create_super_user(session: AsyncSession):
    """Create a superuser with admin privileges."""
    try:
        await user_seeder(session)
        logger.info("Successfully created super user")
    except Exception as error:
        logger.error(f"Error creating super user: {str(error)}", exc_info=True)
        raise


async def manage_database(mode='seed'):
    """Manage a database based on the specified mode."""
    try:
        async with get_db_connection() as session:
            try:
                if mode == 'rebuild':
                    await drop_all_tables(session)
                    await create_tables(session)
                    await run_seeders(session)
                elif mode == 'truncate':
                    await truncate_all_tables(session)
                    await run_seeders(session)
                elif mode == 'seed':
                    await run_seeders(session)
                elif mode == 'create_super_user':
                    await create_super_user(session)
                else:
                    raise ValueError(f"Invalid database management mode: {mode}")

                await session.commit()
                logger.info(f"Database {mode} operation completed successfully")
            except Exception as inner_error:
                await session.rollback()
                raise inner_error
    except Exception as error:
        logger.error(f"Database management process failed: {str(error)}", exc_info=True)
        raise


def db_management_command():
    """Interactive command to manage the database."""
    try:
        print("\nDatabase Management Options:")
        print("1. Seed Data Only (Skip existing)")
        print("2. Truncate Tables and Reseed")
        print("3. Rebuild Tables and Seed")
        print("4. Create Super User")
        print("5. Cancel")

        choice = input("\nEnter your choice (1-5): ")

        if choice == '5':
            print("Operation cancelled")
            return

        mode_map = {
            '1': 'seed',
            '2': 'truncate',
            '3': 'rebuild',
            '4': 'create_super_user'
        }

        if choice not in mode_map:
            print("Invalid choice")
            return

        mode = mode_map[choice]
        warning_messages = {
            'seed': "This will add new data (skipping existing)",
            'truncate': "This will clear ALL existing data",
            'rebuild': "This will DROP ALL tables and rebuild from scratch",
            'create_super_user': "This will create a new super user with admin privileges"
        }

        confirmation = input(f"\nWARNING: {warning_messages[mode]}. Are you sure? (yes/no): ")

        if confirmation.lower() != 'yes':
            print("Operation cancelled")
            return

        print(f"\nExecuting {mode} operation...")
        asyncio.run(manage_database(mode))
        print(f"\nDatabase {mode} operation completed successfully!")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    db_management_command()
