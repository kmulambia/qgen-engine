from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from engine.schemas.base_schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class ApplicationBaseSchema(BaseModel):
    workflow_id: UUID
    workflow_stage_id: Optional[UUID] = None
    applicant_id: UUID
    applicant_workspace_id: UUID
    processed_by_id: Optional[UUID] = None
    processed_by_workspace_id: Optional[UUID] = None
    workflow_metadata: Optional[Dict[str, Any]] = {}
    application_metadata: Optional[Dict[str, Any]] = {}
    applicant_metadata: Optional[Dict[str, Any]] = {}
    workspace_metadata: Optional[Dict[str, Any]] = {}
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reference_application_number: Optional[str] = None
    reference_type: Optional[str] = None
    reference_name: Optional[str] = None


class ApplicationCreateSchema(ApplicationBaseSchema, BaseCreateSchema):
    pass


class ApplicationUpdateSchema(BaseUpdateSchema):
    workflow_stage_id: Optional[UUID] = None
    processed_by_id: Optional[UUID] = None
    processed_by_workspace_id: Optional[UUID] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reference_application_number: Optional[str] = None
    reference_type: Optional[str] = None
    reference_name: Optional[str] = None
    version: Optional[int] = None


class ApplicationSchema(BaseSchema, ApplicationBaseSchema):
    pass
