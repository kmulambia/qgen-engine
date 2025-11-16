from typing import Optional
from pydantic import BaseModel, ConfigDict
from engine.schemas.base_schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema


class AddressBaseSchema(BaseModel):
    name: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    address_line_3: Optional[str] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    physical: Optional[str] = None
    postal: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AddressCreateSchema(AddressBaseSchema, BaseCreateSchema):
    pass


class AddressUpdateSchema(AddressBaseSchema, BaseUpdateSchema):
    name: Optional[str] = None


class AddressSchema(AddressBaseSchema, BaseSchema):
    pass
