from engine.repositories.workflow_repository import WorkflowRepository
from engine.services.base_service import BaseService
from engine.models.workflow_model import WorkflowModel


class WorkflowService(BaseService[WorkflowModel]):
    def __init__(self):
        super().__init__(WorkflowRepository())
