import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from engine.models import RoleModel, PermissionModel, RolePermissionModel
from engine.models import WorkspaceTypeModel
from seeder.dependencies.logging import logger


async def seeder(session: AsyncSession):
    """
    Seeds workspace types from the workspace_types.json configuration file.
    This seeder handles all workspace types defined in the configuration.

    Args:
        session (AsyncSession): The database session to use for seeding
    """
    try:
        # Load workspace types configuration
        config_path = Path(__file__).parent.parent / "config" / "workspace_types.json"
        with open(config_path, "r") as f:
            config = json.load(f)

        for workspace_type_config in config["workspace_types"]:
            # Create or get workspace type
            stmt = select(WorkspaceTypeModel).where(
                WorkspaceTypeModel.name == workspace_type_config["name"]
            )
            result = await session.execute(stmt)
            existing_workspace_type = result.scalar_one_or_none()

            if not existing_workspace_type:
                workspace_type = WorkspaceTypeModel(**workspace_type_config)
                session.add(workspace_type)
                await session.flush()
                logger.info(f"Added workspace type: {workspace_type_config['name']}")
            else:
                logger.info(f"Workspace type already exists: {workspace_type_config['name']}")

        await session.commit()
        logger.info("Workspace type seeding completed successfully")

    except Exception as e:
        logger.error(f"Error during workspace type seeding: {str(e)}")
        raise


async def role_permission_seeder(session: AsyncSession):
    """Seeds the roles and permissions tables with predefined values."""
    # Define permissions
    permissions = [
        {
            "name": "ALL",
            "description": "Wildcard permission for all access rights",
            "code": "*",
            "group": "super-admin"
        },
        {
            "name": "ALL USER MANAGEMENT",
            "description": "user management wildcard permission",
            "code": "user-management.*",
            "group": "user-management"
        },
        # ... other permissions ...
    ]

    # Seed permissions
    for perm in permissions:
        try:
            stmt = select(PermissionModel).where(PermissionModel.code == perm["code"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"Skipping existing permission: {perm['name']}")
                continue

            new_permission = PermissionModel(**perm)
            session.add(new_permission)
            logger.info(f"Added new permission: {perm['name']}")

        except Exception as e:
            logger.error(f"Error processing permission {perm['name']}: {str(e)}")
            raise

    await session.commit()

    # Define roles and their permissions
    roles = [
        {
            "name": "SuperAdmin",
            "description": "Has full system access",
            "is_system_defined": true,
            "permission_codes": ["*"]
        },
        {
            "name": "Admin",
            "description": "Has administrative access",
            "is_system_defined": true,
            "permission_codes": ["user-management.*"]
        },
        {
            "name": "User",
            "description": "Regular user with basic permissions",
            "is_system_defined": false,
            "permission_codes": []
        }
    ]

    # Seed roles and their permissions
    for role_data in roles:
        try:
            # Check if role exists
            stmt = select(RoleModel).where(RoleModel.name == role_data["name"])
            result = await session.execute(stmt)
            existing_role = result.scalar_one_or_none()

            if existing_role:
                logger.info(f"Skipping existing role: {role_data['name']}")
                continue

            # Create new role
            permission_codes = role_data.pop("permission_codes")
            new_role = RoleModel(**role_data)
            session.add(new_role)
            await session.flush()

            # Add role permissions
            if permission_codes:
                perm_stmt = select(PermissionModel).where(
                    PermissionModel.code.in_(permission_codes)
                )
                permissions = (await session.execute(perm_stmt)).scalars().all()

                for perm in permissions:
                    role_perm = RolePermissionModel(
                        role_id=new_role.id,
                        permission_id=perm.id
                    )
                    session.add(role_perm)

            logger.info(f"Added new role: {role_data['name']}")

        except Exception as e:
            logger.error(f"Error processing role {role_data['name']}: {str(e)}")
            raise

    await session.commit()
