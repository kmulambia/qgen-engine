from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema
from engine.schemas.workspace_type_schemas import WorkspaceTypeSchema


class WorkspaceBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    workspace_type_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    reference_name: Optional[str] = None
    reference_type: Optional[str] = None
    reference_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WorkspaceCreateSchema(WorkspaceBaseSchema, BaseCreateSchema):
    pass


class WorkspaceUpdateSchema(WorkspaceBaseSchema, BaseUpdateSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    workspace_type_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    reference_name: Optional[str] = None
    reference_type: Optional[str] = None
    reference_number: Optional[str] = None


class WorkspaceSchema(WorkspaceBaseSchema, BaseSchema):
    workspace_type: Optional[WorkspaceTypeSchema] = None
