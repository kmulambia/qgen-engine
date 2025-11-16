from engine.models.attachment_model import AttachmentModel
from engine.schemas.attachment_schemas import AttachmentSchema, AttachmentCreateSchema, AttachmentUpdateSchema
from engine.schemas.base_schemas import PaginatedResponse
from engine.services.attachment_service import AttachmentService
from api.v1.base_api import BaseAPI


class AttachmentAPI(BaseAPI[AttachmentModel, AttachmentCreateSchema, AttachmentUpdateSchema, AttachmentSchema]):
    def __init__(self):
        super().__init__(AttachmentService(), AttachmentSchema, AttachmentCreateSchema, AttachmentUpdateSchema,
                         AttachmentModel, PaginatedResponse[AttachmentSchema])


attachment_api = AttachmentAPI()
router = attachment_api.router
