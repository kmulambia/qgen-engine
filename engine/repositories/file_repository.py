from engine.models.file_model import FileModel
from engine.repositories.base_repository import BaseRepository


class FileRepository(BaseRepository[FileModel]):
    def __init__(self):
        super().__init__(FileModel)
