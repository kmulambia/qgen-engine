from engine.models.workflow_stage_model import WorkflowStageModel
from engine.schemas.workflow_stage_schemas import WorkflowStageSchema, WorkflowStageCreateSchema, \
    WorkflowStageUpdateSchema
from engine.services.workflow_stage_service import WorkflowStageService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class WorkflowStageAPI(BaseAPI[WorkflowStageModel, WorkflowStageCreateSchema, WorkflowStageUpdateSchema, WorkflowStageSchema]):
    def __init__(self):
        super().__init__(WorkflowStageService(), WorkflowStageSchema, WorkflowStageCreateSchema,
                         WorkflowStageUpdateSchema, WorkflowStageModel, PaginatedResponse[WorkflowStageSchema])


workflow_stage_api = WorkflowStageAPI()
router = workflow_stage_api.router
