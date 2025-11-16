from engine.models.approval_model import ApprovalModel
from engine.schemas.approval_schema import ApprovalSchema, ApprovalCreateSchema, ApprovalUpdateSchema
from engine.schemas.base_schemas import PaginatedResponse
from engine.services.approval_service import ApprovalService
from api.v1.base_api import BaseAPI


class ApprovalAPI(BaseAPI[ApprovalModel, ApprovalCreateSchema, ApprovalUpdateSchema, ApprovalSchema]):
    def __init__(self):
        super().__init__(ApprovalService(), ApprovalSchema, ApprovalCreateSchema, ApprovalUpdateSchema, ApprovalModel,
                         PaginatedResponse[ApprovalSchema])


approval_api = ApprovalAPI()
router = approval_api.router
