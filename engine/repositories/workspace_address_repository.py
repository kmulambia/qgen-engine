from engine.models import WorkspaceAddressModel
from engine.repositories.base_repository import BaseRepository


class WorkspaceAddressRepository(BaseRepository[WorkspaceAddressModel]):
    def __init__(self):
        super().__init__(WorkspaceAddressModel)
