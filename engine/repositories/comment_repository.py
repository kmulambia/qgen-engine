from engine.models.comment_model import CommentModel
from engine.repositories.base_repository import BaseRepository


class CommentRepository(BaseRepository[CommentModel]):
    def __init__(self):
        super().__init__(CommentModel)
