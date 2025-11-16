from engine.models.approval_model import ApprovalModel
from engine.repositories.approval_repository import ApprovalRepository
from engine.services.base_service import BaseService


class ApprovalService(BaseService[ApprovalModel]):
    def __init__(self):
        super().__init__(ApprovalRepository())
