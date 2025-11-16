from typing import Optional

from pydantic import BaseModel, ConfigDict

from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class CredentialBaseSchema(BaseModel):
    password_hash: str
    salt: str
    type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CredentialCreateSchema(CredentialBaseSchema, BaseCreateSchema):
    pass


class CredentialUpdateSchema(CredentialBaseSchema, BaseUpdateSchema):
    password_hash: Optional[str] = None
    salt: Optional[str] = None
    type: Optional[str] = None


class CredentialSchema(CredentialBaseSchema, BaseSchema):
    pass
