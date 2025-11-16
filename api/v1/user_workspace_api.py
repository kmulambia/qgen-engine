from engine.models.user_workspace_model import UserWorkspaceModel
from engine.schemas.user_workspace_schemas import UserWorkspaceSchema, UserWorkspaceCreateSchema, \
    UserWorkspaceUpdateSchema
from engine.services.user_workspace_service import UserWorkspaceService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class UserWorkspaceAPI(BaseAPI[UserWorkspaceModel, UserWorkspaceCreateSchema, UserWorkspaceUpdateSchema, UserWorkspaceSchema]):
    def __init__(self):
        super().__init__(UserWorkspaceService(), UserWorkspaceSchema, UserWorkspaceCreateSchema,
                         UserWorkspaceUpdateSchema, UserWorkspaceModel, PaginatedResponse[UserWorkspaceSchema])


user_workspace_api = UserWorkspaceAPI()
router = user_workspace_api.router
