from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class WorkspaceAddressBaseSchema(BaseModel):
    workspace_id: UUID
    address_id: UUID
    is_primary: bool = False
    is_billing: bool = False
    is_shipping: bool = False

    model_config = ConfigDict(from_attributes=True)


class WorkspaceAddressCreateSchema(WorkspaceAddressBaseSchema, BaseCreateSchema):
    pass


class WorkspaceAddressUpdateSchema(WorkspaceAddressBaseSchema, BaseUpdateSchema):
    workspace_id: Optional[UUID] = None
    address_id: Optional[UUID] = None
    is_primary: Optional[bool] = None
    is_billing: Optional[bool] = None
    is_shipping: Optional[bool] = None


class WorkspaceAddressSchema(WorkspaceAddressBaseSchema, BaseSchema):
    pass
