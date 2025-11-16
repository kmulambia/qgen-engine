from engine.models.client_model import ClientModel
from engine.schemas.client_schemas import ClientSchema, ClientCreateSchema, ClientUpdateSchema
from engine.services.client_service import ClientService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse


class ClientAPI(BaseAPI[ClientModel, ClientCreateSchema, ClientUpdateSchema, ClientSchema]):
    def __init__(self):
        super().__init__(
            ClientService(),
            ClientSchema,
            ClientCreateSchema,
            ClientUpdateSchema,
            ClientModel,
            PaginatedResponse[ClientSchema]
        )


client_api = ClientAPI()
router = client_api.router
