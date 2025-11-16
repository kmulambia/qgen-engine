from engine.models.file_model import FileModel
from engine.repositories.file_repository import FileRepository
from engine.services.base_service import BaseService


class FileService(BaseService[FileModel]):
    def __init__(self):
        super().__init__(FileRepository())
