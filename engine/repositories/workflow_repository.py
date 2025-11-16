from engine.models.workflow_model import WorkflowModel
from engine.repositories.base_repository import BaseRepository


class WorkflowRepository(BaseRepository[WorkflowModel]):
    def __init__(self):
        super().__init__(WorkflowModel) 
