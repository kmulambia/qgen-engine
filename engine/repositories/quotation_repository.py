from engine.repositories.base_repository import BaseRepository
from engine.models.quotation_model import QuotationModel


class QuotationRepository(BaseRepository[QuotationModel]):
    def __init__(self):
        super().__init__(QuotationModel)
