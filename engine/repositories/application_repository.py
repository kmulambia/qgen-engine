from engine.models.application_model import ApplicationModel
from engine.repositories.base_repository import BaseRepository


class ApplicationRepository(BaseRepository[ApplicationModel]):
    def __init__(self):
        super().__init__(ApplicationModel) 
