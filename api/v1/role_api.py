from engine.models.role_model import RoleModel
from engine.schemas.role_schemas import RoleSchema, RoleCreateSchema, RoleUpdateSchema
from engine.schemas.base_schemas import PaginatedResponse
from engine.services.role_service import RoleService
from api.v1.base_api import BaseAPI


class RoleAPI(BaseAPI[RoleModel, RoleCreateSchema, RoleUpdateSchema, RoleSchema]):
    def __init__(self):
        super().__init__(RoleService(), RoleSchema, RoleCreateSchema, RoleUpdateSchema, RoleModel,
                         PaginatedResponse[RoleSchema])


role_api = RoleAPI()
router = role_api.router
