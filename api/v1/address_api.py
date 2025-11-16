from engine.models.address_model import AddressModel
from engine.schemas.address_schemas import AddressSchema, AddressCreateSchema, AddressUpdateSchema
from engine.schemas.base_schemas import PaginatedResponse
from engine.services.address_service import AddressService
from api.v1.base_api import BaseAPI


class AddressAPI(BaseAPI[AddressModel, AddressCreateSchema, AddressUpdateSchema, AddressSchema]):
    def __init__(self):
        super().__init__(AddressService(), AddressSchema, AddressCreateSchema, AddressUpdateSchema, AddressModel,
                         PaginatedResponse[AddressSchema])


address_api = AddressAPI()
router = address_api.router
