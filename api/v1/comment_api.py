from engine.models.comment_model import CommentModel
from engine.schemas.comment_schemas import CommentSchema, CommentCreateSchema, CommentUpdateSchema
from engine.services.comment_service import CommentService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class CommentAPI(BaseAPI[CommentModel, CommentCreateSchema, CommentUpdateSchema, CommentSchema]):
    def __init__(self):
        super().__init__(CommentService(), CommentSchema, CommentCreateSchema, CommentUpdateSchema, CommentModel,
                         PaginatedResponse[CommentSchema])


comment_api = CommentAPI()
router = comment_api.router
