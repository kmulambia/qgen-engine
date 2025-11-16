from engine.models import ApprovalModel
from engine.repositories.base_repository import BaseRepository


class ApprovalRepository(BaseRepository[ApprovalModel]):
    def __init__(self):
        super().__init__(ApprovalModel)
