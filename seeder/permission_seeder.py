import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from engine.models import PermissionModel
from seeder.dependencies.logging import logger


async def seeder(session: AsyncSession):
    """
    Seeds permissions from the permissions.json configuration file.
    This seeder handles all permissions defined in the configuration.

    Args:
        session (AsyncSession): The database session to use for seeding
    """
    try:
        # Load permissions configuration
        config_path = Path(__file__).parent.parent / "config" / "permissions.json"
        with open(config_path, "r") as f:
            config = json.load(f)

        for permission_config in config["permissions"]:
            # Create or get permission
            stmt = select(PermissionModel).where(
                PermissionModel.code == permission_config["code"]
            )
            result = await session.execute(stmt)
            existing_permission = result.scalar_one_or_none()

            if not existing_permission:
                permission = PermissionModel(**permission_config)
                session.add(permission)
                await session.flush()
                logger.info(f"Added permission: {permission_config['name']}")
            else:
                logger.info(f"Permission already exists: {permission_config['name']}")

        await session.commit()
        logger.info("Permission seeding completed successfully")

    except Exception as e:
        logger.error(f"Error during permission seeding: {str(e)}")
        raise
