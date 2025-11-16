from engine.models.application_model import ApplicationModel
from engine.schemas.application_schemas import ApplicationSchema, ApplicationCreateSchema, ApplicationUpdateSchema
from engine.services.application_service import ApplicationService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class ApplicationAPI(BaseAPI[ApplicationModel, ApplicationCreateSchema, ApplicationUpdateSchema, ApplicationSchema]):
    def __init__(self):
        super().__init__(ApplicationService(), ApplicationSchema, ApplicationCreateSchema, ApplicationUpdateSchema,
                         ApplicationModel, PaginatedResponse[ApplicationSchema])


application_api = ApplicationAPI()
router = application_api.router
