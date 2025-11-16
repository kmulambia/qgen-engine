from engine.repositories.application_repository import ApplicationRepository
from engine.services.base_service import BaseService
from engine.models.application_model import ApplicationModel


class ApplicationService(BaseService[ApplicationModel]):
    def __init__(self):
        super().__init__(ApplicationRepository())
