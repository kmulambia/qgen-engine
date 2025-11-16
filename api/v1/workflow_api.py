from engine.models.workflow_model import WorkflowModel
from engine.schemas.workflow_schemas import WorkflowSchema, WorkflowCreateSchema, WorkflowUpdateSchema
from engine.services.workflow_service import WorkflowService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class WorkflowAPI(BaseAPI[WorkflowModel, WorkflowCreateSchema, WorkflowUpdateSchema, WorkflowSchema]):
    def __init__(self):
        super().__init__(WorkflowService(), WorkflowSchema, WorkflowCreateSchema, WorkflowUpdateSchema, WorkflowModel,
                         PaginatedResponse[WorkflowSchema])


workflow_api = WorkflowAPI()
router = workflow_api.router
