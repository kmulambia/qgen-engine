from engine.repositories.base_repository import BaseRepository
from engine.models.workspace_model import WorkspaceModel


class WorkspaceRepository(BaseRepository[WorkspaceModel]):
    def __init__(self):
        super().__init__(WorkspaceModel)
