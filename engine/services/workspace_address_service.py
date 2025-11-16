from engine.models.workspace_address_model import WorkspaceAddressModel
from engine.repositories.workspace_address_repository import WorkspaceAddressRepository
from engine.services.base_service import BaseService


class WorkspaceAddressService(BaseService[WorkspaceAddressModel]):
    def __init__(self):
        super().__init__(WorkspaceAddressRepository())
