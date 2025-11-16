from engine.models import RolePermissionModel
from engine.repositories.base_repository import BaseRepository


class RolePermissionRepository(BaseRepository[RolePermissionModel]):
    def __init__(self):
        super().__init__(RolePermissionModel)
