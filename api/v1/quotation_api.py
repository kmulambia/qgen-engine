from engine.models.quotation_model import QuotationModel
from engine.schemas.quotation_schemas import (
    QuotationSchema, 
    QuotationCreateSchema, 
    QuotationUpdateSchema
)
from engine.services.quotation_service import QuotationService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class QuotationAPI(BaseAPI[QuotationModel, QuotationCreateSchema, QuotationUpdateSchema, QuotationSchema]):
    def __init__(self):
        super().__init__(
            QuotationService(),
            QuotationSchema,
            QuotationCreateSchema,
            QuotationUpdateSchema,
            QuotationModel,
            PaginatedResponse[QuotationSchema]
        )


quotation_api = QuotationAPI()
router = quotation_api.router
