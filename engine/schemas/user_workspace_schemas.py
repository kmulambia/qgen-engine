from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from engine.schemas.role_schemas import RoleSchema
from engine.schemas.workspace_schemas import WorkspaceSchema
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class UserWorkspaceBaseSchema(BaseModel):
    user_id: UUID
    workspace_id: UUID
    role_id: UUID
    is_default: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class UserWorkspaceCreateSchema(UserWorkspaceBaseSchema, BaseCreateSchema):
    pass


class UserWorkspaceUpdateSchema(UserWorkspaceBaseSchema, BaseUpdateSchema):
    user_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    is_default: Optional[bool] = None


class UserWorkspaceSchema(UserWorkspaceBaseSchema, BaseSchema):
    role: Optional[RoleSchema] = None
    workspace: Optional[WorkspaceSchema] = None
