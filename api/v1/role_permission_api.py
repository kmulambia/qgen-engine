from engine.models.role_permission_model import RolePermissionModel
from engine.schemas.role_permission_schemas import RolePermissionSchema, RolePermissionCreateSchema, \
    RolePermissionUpdateSchema
from engine.schemas.base_schemas import PaginatedResponse
from engine.services.role_permission_service import RolePermissionService
from api.v1.base_api import BaseAPI


class RolePermissionAPI(BaseAPI[RolePermissionModel, RolePermissionCreateSchema, RolePermissionUpdateSchema, RolePermissionSchema]):
    def __init__(self):
        super().__init__(RolePermissionService(), RolePermissionSchema, RolePermissionCreateSchema,
                         RolePermissionUpdateSchema, RolePermissionModel, PaginatedResponse[RolePermissionSchema])


role_permission_api = RolePermissionAPI()
router = role_permission_api.router
