from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class AttachmentBaseSchema(BaseModel):
    application_id: UUID
    workflow_id: UUID
    workflow_stage_id: UUID
    file_id: UUID
    uploaded_by: UUID
    name: str
    attachment_metadata: Optional[Dict[str, Any]] = {}


class AttachmentCreateSchema(BaseCreateSchema):
    file_id: Optional[UUID] = None
    name: Optional[str] = None
    attachment_metadata: Optional[Dict[str, Any]] = {}


class AttachmentUpdateSchema(AttachmentBaseSchema, BaseUpdateSchema):
    pass


class AttachmentSchema(AttachmentBaseSchema, BaseSchema):
    pass
