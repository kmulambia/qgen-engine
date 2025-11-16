from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.permission_model import PermissionModel
from engine.schemas.permission_schemas import PermissionSchema, PermissionCreateSchema, PermissionUpdateSchema
from engine.schemas.base_schemas import PaginatedResponse
from engine.services.permission_service import PermissionService
from engine.schemas.token_schemas import TokenData
from api.v1.base_api import BaseAPI
from api.dependencies.db import get_db
from api.dependencies.authentication import authentication
from api.dependencies.ratelimiter import rate_limit


class PermissionAPI(BaseAPI[PermissionModel, PermissionCreateSchema, PermissionUpdateSchema, PermissionSchema]):
    def __init__(self):
        super().__init__(PermissionService(), PermissionSchema, PermissionCreateSchema, PermissionUpdateSchema,
                         PermissionModel, PaginatedResponse[PermissionSchema])

        # Store the /{uid} route before filtering
        uid_route = None
        for route in self.router.routes:
            if route.path == "/{uid}" and "GET" in route.methods:
                uid_route = route
                break

        # Remove all routes except for the read endpoints (excluding /{uid} for now)
        self.router.routes = [
            route for route in self.router.routes
            if (route.path.endswith("/query") or
                route.path.endswith("/count") or
                (route.path == "" and "GET" in route.methods))
        ]

        # Add custom endpoint for getting all groups BEFORE /{uid} route
        self._setup_groups_route()
        
        # Now add back the /{uid} route at the end (so /groups is matched first)
        if uid_route:
            self.router.routes.append(uid_route)

    def _setup_groups_route(self):
        @self.router.get("/groups", response_model=List[str], dependencies=[Depends(rate_limit)])
        async def get_all_groups(
            db_conn: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication)
        ):
            """
            Get all unique group names from permissions.
            
            Returns:
                List[str]: List of unique group names
            """
            return await self.service.get_all_groups(db_conn)


permission_api = PermissionAPI()
router = permission_api.router
