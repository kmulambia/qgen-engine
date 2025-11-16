from typing import Optional

from pydantic import BaseModel, ConfigDict

from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class WorkspaceTypeBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    is_system_defined: Optional[bool] = False
    model_config = ConfigDict(from_attributes=True)


class WorkspaceTypeCreateSchema(WorkspaceTypeBaseSchema, BaseCreateSchema):
    pass


class WorkspaceTypeUpdateSchema(WorkspaceTypeBaseSchema, BaseUpdateSchema):
    name: Optional[str] = None
    is_system_defined: Optional[bool] = None

class WorkspaceTypeSchema(WorkspaceTypeBaseSchema, BaseSchema):
    pass
