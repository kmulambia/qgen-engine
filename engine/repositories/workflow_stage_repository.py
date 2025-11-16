from engine.models.workflow_stage_model import WorkflowStageModel
from engine.repositories.base_repository import BaseRepository


class WorkflowStageRepository(BaseRepository[WorkflowStageModel]):
    def __init__(self):
        super().__init__(WorkflowStageModel)
