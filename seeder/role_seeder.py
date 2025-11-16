import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from engine.models import RoleModel, PermissionModel, RolePermissionModel
from seeder.dependencies.logging import logger


async def seeder(session: AsyncSession):
    """
    Seeds roles and their associated permissions from the roles.json configuration file.
    This seeder handles all roles defined in the configuration, including the SuperAdmin role.

    Args:
        session (AsyncSession): The database session to use for seeding
    """
    try:
        # Load roles configuration
        config_path = Path(__file__).parent.parent / "config" / "roles.json"
        with open(config_path, "r") as f:
            config = json.load(f)

        for role_config in config["roles"]:
            # Create or get role
            stmt = select(RoleModel).where(RoleModel.name == role_config["name"])
            result = await session.execute(stmt)
            existing_role = result.scalar_one_or_none()

            if not existing_role:
                role = RoleModel(
                    name=role_config["name"],
                    description=role_config["description"],
                    is_system_defined=role_config.get("is_system_defined", False)
                )
                session.add(role)
                await session.flush()
                logger.info(f"Added role: {role_config['name']}")
            else:
                role = existing_role
                # Update is_system_defined if it exists in config
                if "is_system_defined" in role_config:
                    role.is_system_defined = role_config["is_system_defined"]
                logger.info(f"Role already exists: {role_config['name']}")

            # Handle permissions for the role
            for permission_config in role_config.get("permissions", []):
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
                    permission_id = permission.id
                else:
                    logger.info(f"Permission already exists: {permission_config['name']}")
                    permission_id = existing_permission.id

                # Ensure role has the permission
                stmt = select(RolePermissionModel).where(
                    RolePermissionModel.role_id == role.id,
                    RolePermissionModel.permission_id == permission_id
                )
                result = await session.execute(stmt)
                existing_role_permission = result.scalar_one_or_none()

                if not existing_role_permission:
                    role_permission = RolePermissionModel(
                        role_id=role.id,
                        permission_id=permission_id
                    )
                    session.add(role_permission)
                    logger.info(f"Added permission {permission_config['name']} to role {role_config['name']}")
                else:
                    logger.info(f"Role {role_config['name']} already has permission {permission_config['name']}")

        await session.commit()
        logger.info("Role seeding completed successfully")

    except Exception as e:
        logger.error(f"Error during role seeding: {str(e)}")
        raise
