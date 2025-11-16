from engine.models import AddressModel
from engine.repositories.base_repository import BaseRepository


class AddressRepository(BaseRepository[AddressModel]):
    def __init__(self):
        super().__init__(AddressModel)
