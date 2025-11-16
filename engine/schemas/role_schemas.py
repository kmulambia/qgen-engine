from typing import Optional

from pydantic import BaseModel, ConfigDict

from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class RoleBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    is_system_defined: bool = False

    model_config = ConfigDict(from_attributes=True)


class RoleCreateSchema(RoleBaseSchema, BaseCreateSchema):
    pass


class RoleUpdateSchema(RoleBaseSchema, BaseUpdateSchema):
    name: Optional[str] = None
    is_system_defined: Optional[bool] = None


class RoleSchema(RoleBaseSchema, BaseSchema):
    pass
