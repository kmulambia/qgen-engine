from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema
from engine.schemas.workspace_schemas import WorkspaceSchema


class WorkflowBaseSchema(BaseModel):
    name: str
    workspace_id: Optional[UUID] = None
    description: Optional[str] = None
    component: str
    expiry_in_days: Optional[int] = None


class WorkflowCreateSchema(WorkflowBaseSchema, BaseCreateSchema):
    pass


class WorkflowUpdateSchema(WorkflowBaseSchema, BaseUpdateSchema):
    name: Optional[str] = None
    workspace_id: Optional[UUID] = None
    description: Optional[str] = None
    component: Optional[str] = None
    expiry_in_days: Optional[int] = None


class WorkflowSchema(WorkflowBaseSchema, BaseSchema):
    workspace: Optional[WorkspaceSchema] = None
