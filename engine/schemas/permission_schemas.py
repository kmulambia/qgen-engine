from typing import Optional

from pydantic import BaseModel, ConfigDict

from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class PermissionBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    group: Optional[str] = None
    code: str

    model_config = ConfigDict(from_attributes=True)


class PermissionCreateSchema(PermissionBaseSchema, BaseCreateSchema):
    pass


class PermissionUpdateSchema(PermissionBaseSchema, BaseUpdateSchema):
    name: Optional[str] = None
    code: Optional[str] = None


class PermissionSchema(PermissionBaseSchema, BaseSchema):
    model_config = ConfigDict(from_attributes=True)
