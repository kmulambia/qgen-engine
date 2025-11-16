from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict

from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema
from engine.schemas.workspace_schemas import WorkspaceBaseSchema


class UserBaseSchema(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    sex: Optional[str] = None
    id_number: Optional[str] = None
    id_type: Optional[str] = None
    date_of_birth: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(UserBaseSchema, BaseCreateSchema):
    password: str


class UserUpdateSchema(UserBaseSchema, BaseUpdateSchema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class UserSchema(UserBaseSchema, BaseSchema):
    pass


class UserRegisterSchema(BaseModel):
    """Schema for user registration with workspace and role assignment"""
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    sex: Optional[str] = None
    id_number: Optional[str] = None
    id_type: Optional[str] = None
    date_of_birth: Optional[date] = None
    password: str
    role_id: UUID
    workspace_id: UUID

    model_config = ConfigDict(from_attributes=True)




