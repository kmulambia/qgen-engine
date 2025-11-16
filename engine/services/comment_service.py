from engine.repositories.comment_repository import CommentRepository
from engine.services.base_service import BaseService
from engine.models.comment_model import CommentModel


class CommentService(BaseService[CommentModel]):
    def __init__(self):
        super().__init__(CommentRepository())
