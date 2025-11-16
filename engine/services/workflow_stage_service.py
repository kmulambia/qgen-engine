from engine.repositories.workflow_stage_repository import WorkflowStageRepository
from engine.services.base_service import BaseService
from engine.models.workflow_stage_model import WorkflowStageModel


class WorkflowStageService(BaseService[WorkflowStageModel]):
    def __init__(self):
        super().__init__(WorkflowStageRepository())
