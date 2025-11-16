from engine.models.client_model import ClientModel
from engine.repositories.client_repository import ClientRepository
from engine.services.base_service import BaseService


class ClientService(BaseService[ClientModel]):
    def __init__(self):
        super().__init__(ClientRepository())
