from engine.models.address_model import AddressModel
from engine.repositories.address_repository import AddressRepository
from engine.services.base_service import BaseService


class AddressService(BaseService[AddressModel]):
    def __init__(self):
        super().__init__(AddressRepository())
