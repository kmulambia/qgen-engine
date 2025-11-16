from engine.models.workspace_model import WorkspaceModel
from engine.schemas.workspace_schemas import WorkspaceSchema, WorkspaceCreateSchema, WorkspaceUpdateSchema
from engine.services.workspace_service import WorkspaceService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class WorkspaceAPI(BaseAPI[WorkspaceModel, WorkspaceCreateSchema, WorkspaceUpdateSchema, WorkspaceSchema]):
    def __init__(self):
        super().__init__(WorkspaceService(), WorkspaceSchema, WorkspaceCreateSchema, WorkspaceUpdateSchema,
                         WorkspaceModel, PaginatedResponse[WorkspaceSchema])


workspace_api = WorkspaceAPI()
router = workspace_api.router
