from engine.models import PermissionModel
from engine.repositories.base_repository import BaseRepository


class PermissionRepository(BaseRepository[PermissionModel]):
    def __init__(self):
        super().__init__(PermissionModel)
