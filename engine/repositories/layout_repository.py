from engine.models.layout_model import LayoutModel
from engine.repositories.base_repository import BaseRepository


class LayoutRepository(BaseRepository[LayoutModel]):
    """Repository for layout operations"""
    
    def __init__(self):
        super().__init__(LayoutModel)
        # Define searchable fields for the layout model
        self.searchable_fields = [
            "name",
            "description",
            "company_name",
            "reference_number",
            "email",
            "phone",
            "notes"
        ]
