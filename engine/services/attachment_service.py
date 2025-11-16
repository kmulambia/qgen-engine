from engine.models.attachment_model import AttachmentModel
from engine.repositories.attachment_repository import AttachmentRepository
from engine.services.base_service import BaseService


class AttachmentService(BaseService[AttachmentModel]):
    def __init__(self):
        super().__init__(AttachmentRepository())
