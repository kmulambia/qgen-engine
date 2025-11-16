from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class AuditBaseSchema(BaseModel):
    user_id: Optional[UUID] = None
    action: str
    user_metadata: Optional[Dict[str, Any]] = None
    entity_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class AuditCreateSchema(BaseCreateSchema):
    pass


class AuditUpdateSchema(AuditBaseSchema, BaseUpdateSchema):
    action: Optional[str] = None
    user_metadata: Optional[Dict[str, Any]] = None
    entity_metadata: Optional[Dict[str, Any]] = None


class AuditSchema(AuditBaseSchema, BaseSchema):
    pass


class UserSecuritySummarySchema(BaseModel):
    """
    Optimized schema for user security information.
    Returns all security-related data in a single response.
    """
    last_login: Optional[AuditSchema] = None
    last_password_reset: Optional[AuditSchema] = None
    failed_login_count: int = 0

    model_config = ConfigDict(from_attributes=True)

