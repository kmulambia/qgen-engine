from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from engine.schemas.base_schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class ApprovalBaseSchema(BaseModel):
    application_id: UUID
    workflow_id: UUID
    workflow_stage_id: UUID
    approver_id: UUID
    decision: str = Field(default='pending')
    comments: Optional[str] = None
    approval_metadata: Dict[str, Any] = Field(default_factory=dict)


class ApprovalCreateSchema(ApprovalBaseSchema, BaseCreateSchema):
    pass


class ApprovalUpdateSchema(ApprovalBaseSchema, BaseUpdateSchema):
    decision: Optional[str] = None
    comments: Optional[str] = None
    approval_metadata: Optional[Dict[str, Any]] = None


class ApprovalSchema(ApprovalBaseSchema, BaseSchema):
    pass
