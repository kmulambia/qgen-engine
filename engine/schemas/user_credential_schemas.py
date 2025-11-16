from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class UserCredentialBaseSchema(BaseModel):
    user_id: UUID
    credential_id: UUID

    model_config = ConfigDict(from_attributes=True)


class UserCredentialCreateSchema(UserCredentialBaseSchema, BaseCreateSchema):
    pass


class UserCredentialUpdateSchema(UserCredentialBaseSchema, BaseUpdateSchema):
    user_id: Optional[UUID] = None
    credential_id: Optional[UUID] = None


class UserCredentialSchema(UserCredentialBaseSchema, BaseSchema):
    pass
