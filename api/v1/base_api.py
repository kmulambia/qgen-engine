from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from engine.schemas.token_schemas import TokenData
from engine.services.base_service import BaseService
from engine.schemas.base_schemas import BaseSchema, PaginatedResponse, FilterCondition, CountResponse, BaseCreateSchema, \
    BaseUpdateSchema, FilterParams
from typing import Generic, List, Optional, Type, TypeVar
from api.dependencies.authentication import authentication
from api.dependencies.ratelimiter import rate_limit
from api.dependencies.logging import logger
from api.dependencies.db import get_db
from engine.utils.config_util import load_config
from engine.models.base_model import BaseModel

config = load_config()
MODE = config.get_variable("MODE", "development")

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseCreateSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseUpdateSchema)
SchemaType = TypeVar("SchemaType", bound=BaseSchema)


class BaseAPI(Generic[ModelType, CreateSchemaType, UpdateSchemaType, SchemaType]):
    def __init__(
            self,
            service: BaseService[ModelType],
            response_model: Type[SchemaType],
            create_schema: Type[CreateSchemaType],
            update_schema: Type[UpdateSchemaType],
            model_type: Type[ModelType],
            paginated_response_model: Optional[Type[PaginatedResponse[SchemaType]]] = None,
    ):
        self.service = service
        self.response_model = response_model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.model_type = model_type
        self.paginated_response_model = paginated_response_model
        self.router = APIRouter()
        
        # Define router methods
        self._setup_routes()

    async def _load_relationships_safely(self, db_conn: AsyncSession, model):
        """Safely load relationships for a model in the async context."""
        try:
            # Get the model class to check for relationships
            model_class = type(model)
            if hasattr(model_class, '__mapper__'):
                relationships = model_class.__mapper__.relationships
                if relationships:
                    # Create a query to reload the model with relationships
                    from sqlalchemy.orm import selectinload
                    from sqlalchemy import select
                    
                    # Build selectinload options for all relationships
                    load_options = []
                    for relationship in relationships:
                        try:
                            relationship_attr = getattr(model_class, relationship.key)
                            load_options.append(selectinload(relationship_attr))
                        except Exception as e:
                            logger.warning(f"Could not create load option for {relationship.key}: {e}")
                            continue
                    
                    if load_options:
                        # Reload the model with relationships
                        query = select(model_class).where(model_class.id == model.id)
                        for option in load_options:
                            query = query.options(option)
                        
                        result = await db_conn.execute(query)
                        loaded_model = result.unique().scalar_one_or_none()
                        if loaded_model:
                            # Copy relationship data to the original model
                            for relationship in relationships:
                                try:
                                    if hasattr(loaded_model, relationship.key):
                                        setattr(model, relationship.key, getattr(loaded_model, relationship.key))
                                except Exception as e:
                                    logger.warning(f"Could not copy relationship {relationship.key}: {e}")
                                    continue
                                    
        except Exception as e:
            logger.warning(f"Error loading relationships: {e}")
            # Continue without relationships if loading fails

    def _create_safe_response_dict(self, model):
        """Create a safe response dict when validation fails."""
        try:
            # Create a basic response with core fields
            response_dict = {
                'id': getattr(model, 'id', None),
                'created_at': getattr(model, 'created_at', None),
                'updated_at': getattr(model, 'updated_at', None),
                'status': getattr(model, 'status', None),
            }
            
            # Add model-specific fields
            for field_name in self.response_model.model_fields:
                try:
                    if hasattr(model, field_name):
                        value = getattr(model, field_name)
                        if value is not None:
                            response_dict[field_name] = value
                except Exception:
                    continue
            
            return response_dict
            
        except Exception as e:
            logger.error(f"Error creating safe response dict: {e}")
            return {"id": getattr(model, 'id', None), "status": "created"}

    def _setup_routes(self):
        """Setup all the router endpoints."""
        
        @self.router.post("", response_model=self.response_model, status_code=status.HTTP_201_CREATED)
        @rate_limit()
        async def create_item(
                request: Request,
                data: self.create_schema,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication),
        ):
            try:
                # Log the incoming data for debugging
                logger.info(f"Creating item with data: {data.model_dump()}")
                
                # Validate UUID fields before model creation
                try:
                    model_data = self.model_type(**data.model_dump())
                except Exception as model_error:
                    logger.error(f"Error creating model instance: {model_error}")
                    logger.error(f"Data that failed: {data.model_dump()}")
                    raise HTTPException(status_code=400, detail=f"Invalid data format: {str(model_error)}")
                
                model = await self.service.create(db_conn, model_data, token_data)
                
                # Load relationships safely in the async context
                await self._load_relationships_safely(db_conn, model)
                
                # Now validate with the fully loaded model
                try:
                    return self.response_model.model_validate(model)
                except Exception as validation_error:
                    logger.error(f"Validation error after creation: {validation_error}")
                    # Fallback to dict representation if validation fails
                    return self._create_safe_response_dict(model)
                
            except Exception as e:
                error_details = str(e) if MODE == "development" else "An error occurred while creating the item."
                logger.error(f"Error creating item: {e}, Request: {request.method} {request.url}")
                raise HTTPException(status_code=500, detail=error_details)

        @self.router.get("/{uid}", response_model=self.response_model)
        @rate_limit()
        async def read_item(
                request: Request,
                uid: UUID,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication)  # noqa
        ):
            try:
                model = await self.service.get_by_id(db_conn, uid)
                if not model:
                    raise HTTPException(status_code=404, detail="Item not found")
                
                # Load relationships safely in the async context
                await self._load_relationships_safely(db_conn, model)
                
                # Now validate with the fully loaded model
                try:
                    return self.response_model.model_validate(model)
                except Exception as validation_error:
                    logger.error(f"Validation error after reading: {validation_error}")
                    # Fallback to dict representation if validation fails
                    return self._create_safe_response_dict(model)
                
            except Exception as e:
                error_details = str(e) if MODE == "development" else "An error occurred while reading item."
                logger.error(f"Error: {e}, Request: {request.method} {request.url}")
                raise HTTPException(status_code=500, detail=error_details)

        @self.router.put("/{uid}", response_model=self.response_model)
        @self.router.patch("/{uid}", response_model=self.response_model)
        @rate_limit()
        async def update_item(
                request: Request,
                uid: UUID,
                data: self.update_schema,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication),
        ):
            try:
                model_data = self.model_type(**data.model_dump())
                model = await self.service.update(db_conn, uid, model_data, token_data)

                if not model:
                    raise HTTPException(status_code=404, detail="Item not found")
                
                # Load relationships safely in the async context
                await self._load_relationships_safely(db_conn, model)
                
                # Now validate with the fully loaded model
                try:
                    return self.response_model.model_validate(model)
                except Exception as validation_error:
                    logger.error(f"Validation error after update: {validation_error}")
                    # Fallback to dict representation if validation fails
                    return self._create_safe_response_dict(model)

            except Exception as e:
                error_details = str(e) if MODE == "development" else "An error occurred while updating the item."
                logger.error(f"Error: {e}, Request: {request.method} {request.url}")
                raise HTTPException(status_code=500, detail=error_details)

        @self.router.get("", response_model=self.paginated_response_model)
        @rate_limit()
        async def list_items(
                request: Request,
                page: int = 1,
                size: int = 10,
                search: str = "",
                sort_field: str = "",
                sort_direction: str = "asc",
                include_deleted: bool = False,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication)
        ):
            try:
                filter_params = FilterParams(
                    limit=size,
                    offset=(page - 1) * size,
                    search=search,
                    sort_field=sort_field,
                    sort_direction=sort_direction,
                    include_deleted=include_deleted
                )
                filter_response = await self.service.get_all(db_conn=db_conn, params=filter_params, filters=None,
                                                             token_data=token_data)
                
                # Convert items to dict representations to avoid relationship loading issues
                validated_items = []
                for item in filter_response.items:
                    # Load relationships safely for each item
                    await self._load_relationships_safely(db_conn, item)
                    
                    # Now validate with the fully loaded model
                    try:
                        validated_items.append(self.response_model.model_validate(item))
                    except Exception as validation_error:
                        logger.warning(f"Validation error for item {item.id}: {validation_error}")
                        # Fallback to safe response dict
                        validated_items.append(self._create_safe_response_dict(item))
                
                return PaginatedResponse[self.response_model](  # Noqa
                    items=validated_items,
                    total=filter_response.total,
                    page=page,
                    size=size,
                    pages=((filter_response.total - 1) // size) + 1 if filter_response.total > 0 else 0,
                    has_next=((page - 1) * size + len(filter_response.items)) < filter_response.total,
                    has_prev=page > 1
                )
            except Exception as e:
                error_details = str(e) if MODE == "development" else "An error occurred while listing items."
                logger.error(f"Error: {e}, Request: {request.method} {request.url}")
                raise HTTPException(status_code=500, detail=error_details)

        @self.router.post(
            "/query",
            response_model=self.paginated_response_model,
            description="""
            Query items with filters for fields: e.g. [{"field": "name", "operator": "eq", "value": "John"}]
            """
        )
        @rate_limit()
        async def query_items(
                request: Request,
                filters: Optional[List[FilterCondition]] = None,
                page: int = 1,
                size: int = 10,
                search: str = "",
                sort_field: str = "",
                sort_direction: str = "asc",
                include_deleted: bool = False,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication)
        ):
            try:
                filter_params = FilterParams(
                    limit=size,
                    offset=(page - 1) * size,
                    search=search,
                    sort_field=sort_field,
                    sort_direction=sort_direction,
                    include_deleted=include_deleted
                )
                filter_response = await self.service.get_all(db_conn=db_conn, params=filter_params, filters=filters,
                                                             token_data=token_data)
                
                # Convert items to dict representations to avoid relationship loading issues
                validated_items = []
                for item in filter_response.items:
                    # Load relationships safely for each item
                    await self._load_relationships_safely(db_conn, item)
                    
                    # Now validate with the fully loaded model
                    try:
                        validated_items.append(self.response_model.model_validate(item))
                    except Exception as validation_error:
                        logger.warning(f"Validation error for item {item.id}: {validation_error}")
                        # Fallback to safe response dict
                        validated_items.append(self._create_safe_response_dict(item))
                
                return PaginatedResponse[self.response_model](  # Noqa
                    items=validated_items,
                    total=filter_response.total,
                    page=page,
                    size=size,
                    pages=((filter_response.total - 1) // size) + 1 if filter_response.total > 0 else 0,
                    has_next=((page - 1) * size + len(filter_response.items)) < filter_response.total,
                    has_prev=page > 1
                )
            except Exception as e:
                error_message = str(e)
                safe_message = error_message if MODE == "development" else "An error occurred while querying items."
                logger.error(f"Error: {error_message}, Request: {request.method} {request.url}")

                if "duplicate key value" in error_message.lower():
                    raise HTTPException(status_code=409, detail="Duplicate entry found.")
                else:
                    raise HTTPException(status_code=500, detail=safe_message)

        @self.router.post("/count", response_model=CountResponse)
        @rate_limit()
        async def count_items(
                request: Request,
                filters: Optional[List[FilterCondition]] = None,
                include_deleted: bool = False,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication)
        ):
            try:
                count = await self.service.count(db_conn=db_conn, filters=filters, include_deleted=include_deleted,
                                                 token_data=token_data)
                return CountResponse(count=count)
            except Exception as e:
                error_details = str(e) if MODE == "development" else "An error occurred while counting items."
                logger.error(f"Error: {e}, Request: {request.method} {request.url}")
                raise HTTPException(status_code=500, detail=error_details)

        @self.router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
        @rate_limit()
        async def delete_item(
                request: Request,
                uid: UUID,
                hard_delete: Optional[bool] = False,
                db_conn: AsyncSession = Depends(get_db),
                token_data: TokenData = Depends(authentication),
        ):
            try:
                response = await self.service.delete(db_conn=db_conn, uid=uid, hard_delete=hard_delete,
                                                     token_data=token_data)
                if not response:
                    raise HTTPException(status_code=404, detail="Item not found")
            except Exception as e:
                error_details = str(e) if MODE == "development" else "An error occurred while deleting the item."
                logger.error(f"Error: {e}, Request: {request.method} {request.url}")
                raise HTTPException(status_code=500, detail=error_details)
