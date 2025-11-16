from engine.repositories.base_repository import BaseRepository
from engine.models.client_model import ClientModel


class ClientRepository(BaseRepository[ClientModel]):
    def __init__(self):
        super().__init__(ClientModel)
