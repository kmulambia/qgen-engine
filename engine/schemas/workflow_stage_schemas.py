from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema
from engine.schemas.permission_schemas import PermissionSchema
from engine.schemas.workflow_schemas import WorkflowSchema
from pydantic import ConfigDict


class WorkflowStageBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_id: UUID
    sequence: int
    type: Optional[str] = None
    permission_id: Optional[UUID] = None


class WorkflowStageCreateSchema(WorkflowStageBaseSchema, BaseCreateSchema):
    pass


class WorkflowStageUpdateSchema(WorkflowStageBaseSchema, BaseUpdateSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    sequence: Optional[int] = None
    type: Optional[str] = None
    permission_id: Optional[UUID] = None


class WorkflowStageSchema(WorkflowStageBaseSchema, BaseSchema):
    permission: Optional[PermissionSchema] = None
    workflow: Optional[WorkflowSchema] = None

    model_config = ConfigDict(from_attributes=True)
