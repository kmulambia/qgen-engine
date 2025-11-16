from datetime import date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime

from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema
from engine.schemas.workspace_schemas import WorkspaceBaseSchema
from engine.schemas.user_schemas import UserRegisterSchema


class SelfRegisterSchema(UserRegisterSchema):
    """Schema for self-registration - inherits from UserRegisterSchema but makes role_id and workspace_id optional"""
    role_id: Optional[UUID] = None
    workspace: Optional[WorkspaceBaseSchema] = None

    model_config = ConfigDict(from_attributes=True)


class LoginSchema(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeSchema(BaseModel):
    """Schema for password change"""
    user_id: UUID
    password: str

    model_config = ConfigDict(from_attributes=True)


class SessionUserSchema(BaseModel):
    """Simplified user schema specifically for session"""
    id: UUID
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class SessionTokenSchema(BaseModel):
    """Simplified token schema specifically for session"""
    jwt_token: str
    token_type: str
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionWorkspaceTypeSchema(BaseModel):
    """Simplified workspace type schema specifically for session"""
    id: UUID
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SessionWorkspaceSchema(BaseModel):
    """Simplified workspace schema specifically for session"""
    id: UUID
    name: str
    description: Optional[str] = None
    workspace_type: Optional[SessionWorkspaceTypeSchema] = None

    model_config = ConfigDict(from_attributes=True)


class SessionUserWorkspaceSchema(BaseModel):
    """Simplified user workspace schema specifically for session"""
    id: UUID
    workspace: SessionWorkspaceSchema

    model_config = ConfigDict(from_attributes=True)


class SessionRoleSchema(BaseModel):
    """Simplified role schema specifically for session"""
    id: UUID
    name: str
    description: Optional[str] = None
    is_system_defined: bool

    model_config = ConfigDict(from_attributes=True)


class SessionPermissionSchema(BaseModel):
    """Simplified permission schema specifically for session"""
    id: UUID
    name: str
    description: str
    group: str
    code: str

    model_config = ConfigDict(from_attributes=True)


class SessionSchema(BaseModel):
    """Modified session schema to match example output"""
    user: Optional[SessionUserSchema] = None
    token: Optional[SessionTokenSchema] = None
    current_workspace: Optional[SessionUserWorkspaceSchema] = None
    role: Optional[SessionRoleSchema] = None
    permissions: Optional[List[SessionPermissionSchema]] = None
    user_workspaces: Optional[List[SessionUserWorkspaceSchema]] = None

    model_config = ConfigDict(from_attributes=True)


class OTPRequestSchema(BaseModel):
    """Schema for OTP request"""
    email: EmailStr
    otp_type: str


class PasswordResetSchema(BaseModel):
    """Schema for password reset with OTP verification"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
