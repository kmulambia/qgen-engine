from engine.models.workspace_model import WorkspaceModel
from engine.repositories.workspace_repository import WorkspaceRepository
from engine.services.base_service import BaseService


class WorkspaceService(BaseService[WorkspaceModel]):
    def __init__(self):
        super().__init__(WorkspaceRepository())
