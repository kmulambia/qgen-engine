from engine.models.workspace_address_model import WorkspaceAddressModel
from engine.schemas.workspace_address_schemas import WorkspaceAddressSchema, WorkspaceAddressCreateSchema, \
    WorkspaceAddressUpdateSchema
from engine.services.workspace_address_service import WorkspaceAddressService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class WorkspaceAddressAPI(BaseAPI[WorkspaceAddressModel, WorkspaceAddressCreateSchema, WorkspaceAddressUpdateSchema, WorkspaceAddressSchema]):
    def __init__(self):
        super().__init__(WorkspaceAddressService(), WorkspaceAddressSchema, WorkspaceAddressCreateSchema,
                         WorkspaceAddressUpdateSchema, WorkspaceAddressModel, PaginatedResponse[WorkspaceAddressSchema])


workspace_address_api = WorkspaceAddressAPI()
router = workspace_address_api.router
