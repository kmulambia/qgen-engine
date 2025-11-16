from engine.models.workspace_type_model import WorkspaceTypeModel
from engine.schemas.workspace_type_schemas import WorkspaceTypeSchema, WorkspaceTypeCreateSchema, \
    WorkspaceTypeUpdateSchema
from engine.services.workspace_type_service import WorkspaceTypeService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class WorkspaceTypeAPI(BaseAPI[WorkspaceTypeModel, WorkspaceTypeCreateSchema, WorkspaceTypeUpdateSchema, WorkspaceTypeSchema]):
    def __init__(self):
        super().__init__(WorkspaceTypeService(), WorkspaceTypeSchema, WorkspaceTypeCreateSchema,
                         WorkspaceTypeUpdateSchema, WorkspaceTypeModel, PaginatedResponse[WorkspaceTypeSchema])


workspace_type_api = WorkspaceTypeAPI()
router = workspace_type_api.router
