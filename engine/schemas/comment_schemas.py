from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from engine.schemas.base_schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class CommentBaseSchema(BaseModel):
    title: str
    message: str
    workflow_id: UUID
    workflow_stage_id: UUID
    application_id: UUID
    sender_id: UUID
    recipient_id: UUID
    is_read: bool


class CommentCreateSchema(CommentBaseSchema, BaseCreateSchema):
    pass


class CommentUpdateSchema(CommentBaseSchema, BaseUpdateSchema):
    title: Optional[str] = None
    message: Optional[str] = None
    is_read: Optional[bool] = None


class CommentSchema(CommentBaseSchema, BaseSchema):
    pass
