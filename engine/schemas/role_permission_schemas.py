from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from engine.schemas.permission_schemas import PermissionSchema
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class RolePermissionBaseSchema(BaseModel):
    role_id: UUID
    permission_id: UUID

    model_config = ConfigDict(from_attributes=True)


class RolePermissionCreateSchema(RolePermissionBaseSchema, BaseCreateSchema):
    pass


class RolePermissionUpdateSchema(RolePermissionBaseSchema, BaseUpdateSchema):
    role_id: Optional[UUID] = None
    permission_id: Optional[UUID] = None


class RolePermissionSchema(RolePermissionBaseSchema, BaseSchema):
    permission: Optional[PermissionSchema] = None
