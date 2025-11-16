"""
 * Framework - Backend and Services
 * MIT License
 * Copyright (c) 2024 Umodzi Source
"""
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from engine.models import WorkspaceModel, WorkspaceTypeModel
from seeder.dependencies.logging import logger


async def create_workspace(
        session: AsyncSession,
        name: str,
        description: str,
        workspace_type_name: str,
        reference_number: str = None
):
    """
    Create a workspace with the specified type if it doesn't already exist.
    
    Args:
        session (AsyncSession): The database session to use
        name (str): Name of the workspace
        description (str): Description of the workspace
        workspace_type_name (str): Name of the workspace type
        reference_number (str, optional): Reference number for the workspace
    
    Returns:
        WorkspaceModel: Created or existing workspace
    """
    # First check if workspace already exists
    stmt = select(WorkspaceModel).where(WorkspaceModel.name == name)
    result = await session.execute(stmt)
    existing_workspace = result.scalar_one_or_none()

    if existing_workspace:
        logger.info(f"Workspace already exists: {name}")
        return existing_workspace

    # Find the workspace type
    stmt = select(WorkspaceTypeModel).where(
        WorkspaceTypeModel.name == workspace_type_name
    )
    result = await session.execute(stmt)
    workspace_type = result.scalar_one_or_none()

    if not workspace_type:
        logger.error(f"Workspace type not found: {workspace_type_name}")
        raise ValueError(f"Workspace type '{workspace_type_name}' not found")

    # Create the workspace
    workspace = WorkspaceModel(
        name=name,
        description=description,
        workspace_type_id=workspace_type.id,
        reference_number=reference_number
    )
    session.add(workspace)
    await session.flush()
    logger.info(f"Created workspace: {name}")

    return workspace


async def seeder(session: AsyncSession):
    """
    Seeds workspaces based on workspace types from the workspaces.json configuration file.
    
    Args:
        session (AsyncSession): The database session to use for seeding
    """
    try:
        # Load workspaces configuration
        config_path = Path(__file__).parent.parent / "config" / "workspaces.json"
        with open(config_path, "r") as f:
            config = json.load(f)

        # Create workspaces from configuration
        for workspace_config in config["workspaces"]:
            await create_workspace(
                session=session,
                name=workspace_config["name"],
                description=workspace_config["description"],
                workspace_type_name=workspace_config["workspace_type"],
                reference_number=workspace_config.get("reference_number")
            )

        await session.commit()
        logger.info("Workspace seeding completed successfully")

    except Exception as e:
        logger.error(f"Error during workspace seeding: {str(e)}")
        await session.rollback()
        raise
