from engine.models import CredentialModel
from engine.repositories.base_repository import BaseRepository


class CredentialRepository(BaseRepository[CredentialModel]):
    def __init__(self):
        super().__init__(CredentialModel)
