from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class TokenBaseSchema(BaseModel):
    jwt_token: str
    user_id: UUID
    token_type: str
    expires_at: datetime
    last_used_at: Optional[datetime] = None
    last_ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)


class TokenCreateSchema(TokenBaseSchema, BaseCreateSchema):
    pass


class TokenUpdateSchema(TokenBaseSchema, BaseUpdateSchema):
    jwt_token: Optional[str] = None
    token_type: Optional[str] = None
    last_used_at: Optional[datetime] = None
    last_ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: Optional[str] = None


class TokenSchema(TokenBaseSchema, BaseSchema):
    pass


class SessionTokenSchema(BaseModel):
    jwt_token: str
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    """Schema for token data"""
    user_id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    workspace_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "john",
                "last_name": "doe",
                "email": "johndoe@email.com",
                "role_id": "123e4567-e89b-12d3-a456-426614174002",
                "workspace_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }
    )
