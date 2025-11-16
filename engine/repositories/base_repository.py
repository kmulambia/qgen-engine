from datetime import datetime
from typing import Generic, TypeVar, Optional, List, Type, Union, Dict
from uuid import UUID
from sqlalchemy import select, update, delete, and_, not_, desc, asc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.orm import selectinload
from engine.schemas.base_schemas import FilterCondition, FilterParams, FilterResponse, VersionSchema
from engine.utils.datetime_util import parse_sqlserver_datetime_aware

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Base repository for all models

    Attributes:
        model: Model to be used
        searchable_fields: List of fields to be used for searching

    Methods:
        create: Create a new record
        update: Update an existing record
        delete: Delete a record
        get_by_id: Get a record by id
        get_all: Get all records
        count: Count records
        _apply_filters: Apply filters to query
    """
    searchable_fields: List[str] = []

    def __init__(self, model: Type[ModelType]):
        self.model = model
        self.searchable_fields = [field.name for field in self.model.__table__.columns]

    # noinspection PyUnusedLocal
    async def create(self, db_conn: AsyncSession, data: Union[ModelType, Dict]) -> ModelType:
        """Create a new record with proper error handling.
        
        Args:
            db_conn: Database session
            data: Model instance or dictionary to create
            auto_commit: Whether to automatically commit (default True). 
                        Set to False for nested operations like audit logging.
        """
        try:
            if isinstance(data, dict):
                # Filter out any None values and ensure proper model creation
                filtered_data = {k: v for k, v in data.items() if v is not None}
                model = self.model(**filtered_data)
            else:
                model = data

            # Add the model to the session
            db_conn.add(model)

            # Flush to get the ID without committing
            await db_conn.flush()

            # Refresh the model to get all generated values
            await db_conn.refresh(model)

      

            return model

        except Exception as e:
    
            raise e

    @staticmethod
    async def bulk_create(
            db_conn: AsyncSession,
            data: List[ModelType]
    ) -> Dict[str, List[ModelType]]:
        """
        Bulk create records with individual success/failure tracking.
        Uses savepoints to handle individual record failures.
        """
        successful_records = []
        failed_records = []
        
        for record in data:
            # Create a savepoint for each record
            async with db_conn.begin_nested():
                try:
                    db_conn.add(record)
                    await db_conn.flush([record])
                    successful_records.append(record)
                except Exception as e:
                    failed_records.append({
                        "record": record,
                        "error": str(e)
                    })
                    # Savepoint will automatically rollback on exception
                    continue
        
        # Commit all successful records
        try:
            if successful_records:
                await db_conn.commit()
        except Exception as e:
            await db_conn.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error committing bulk create: {e}")
            raise
            
        return {
            "successful": successful_records,
            "failed": failed_records
        }

    async def update(self, db_conn: AsyncSession, uid: UUID, data: ModelType) -> Optional[ModelType]:
        """Update an existing record with proper error handling."""
        try:
            column_names = {column.name for column in self.model.__table__.columns}
            # Only include fields that are not None and exist in the model
            # This prevents overwriting existing data with None values
            update_data = {
                key: value 
                for key, value in data.__dict__.items() 
                if key in column_names and value is not None and not key.startswith('_')
            }
            
            # Always update the updated_at timestamp if it exists
            if 'updated_at' in column_names and 'updated_at' not in update_data:
                from datetime import datetime, timezone
                update_data['updated_at'] = datetime.now(timezone.utc)
            
            statement = (
                update(self.model).where(and_(self.model.id == uid)).values(update_data).returning(self.model)
            )
            result = await db_conn.execute(statement)
            await db_conn.commit()
            updated_data = result.scalar_one_or_none()
            return updated_data
        except Exception as e:
            # Rollback on error
            try:
                await db_conn.rollback()
            except Exception:
                pass
            
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in update method: {e}")
            raise

    async def delete(self, db_conn: AsyncSession, uid: UUID, hard_delete: bool = False) -> bool:
        """Delete a record with proper error handling."""
        try:
            if hard_delete:
                query = (
                    delete(self.model)
                    .where(and_(
                        self.model.id == uid,
                        self.model.is_deleted.is_(False)
                    ))
                    .returning(self.model)
                )
            else:
                query = (
                    update(self.model)
                    .where(and_(
                        self.model.id == uid,
                        self.model.is_deleted.is_(False)
                    ))
                    .values(is_deleted=True)
                    .returning(self.model)
                )

            result = await db_conn.execute(query)
            await db_conn.commit()
            success = result.scalar_one_or_none() is not None

            return success
        except Exception as e:
            # Rollback on error
            try:
                await db_conn.rollback()
            except Exception:
                pass
            
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in delete method: {e}")
            raise

    async def get_by_id(
            self,
            db_conn: AsyncSession,
            uid: UUID,
    ) -> Optional[ModelType]:
        query = (
            select(self.model)
            .where(and_(
                self.model.id == uid,
                self.model.is_deleted.is_(False)
            ))
        )
        # Load relationships safely
        if hasattr(self.model, '__mapper__'):
            relationships = self.model.__mapper__.relationships
            if relationships:
                for relationship in relationships:
                    try:
                        relationship_attr = getattr(self.model, relationship.key)
                        query = query.options(selectinload(relationship_attr))
                    except Exception as e: # noqa
                        # Log relationship loading errors but continue
                        continue

        result = await db_conn.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_all(
            self,
            db_conn: AsyncSession,
            params: Optional[FilterParams] = None,
            filters: Optional[List[FilterCondition]] = None
    ) -> FilterResponse[ModelType]:
        try:
            query = select(self.model)
            if params and params.versioned:
                latest_versions = (
                    select(
                        self.model.reference_name,
                        self.model.reference_number,
                        self.model.reference_type,
                        func.max(self.model.version).label('max_version')
                    )
                    .where(self.model.is_deleted.is_(False))
                    .group_by(
                        self.model.reference_name,
                        self.model.reference_number,
                        self.model.reference_type
                    )
                    .having(
                        and_(
                            self.model.reference_name.isnot(None),
                            self.model.reference_number.isnot(None),
                            self.model.reference_type.isnot(None)
                        )
                    )
                    .subquery()
                )
                query = (
                    select(self.model)
                    .join(
                        latest_versions,
                        and_(
                            self.model.reference_name == latest_versions.c.reference_name,
                            self.model.reference_number == latest_versions.c.reference_number,
                            self.model.reference_type == latest_versions.c.reference_type,
                            self.model.version == latest_versions.c.max_version
                        )
                    )
                )

            # Load relationships safely
            if hasattr(self.model, '__mapper__'):
                relationships = self.model.__mapper__.relationships
                if relationships:
                    for relationship in relationships:
                        try:
                            relationship_attr = getattr(self.model, relationship.key)
                            query = query.options(selectinload(relationship_attr))
                        except Exception as e: # noqa
                            # Log relationship loading errors but continue
                            continue

            # Add search if it exists
            if params and params.search and self.searchable_fields:
                search_conditions = []
                for field in self.searchable_fields:
                    column = getattr(self.model, field, None)
                    if column is not None:
                        # Get the SQL type of the column
                        python_type = column.type.python_type

                        # Handle different column types
                        if python_type == bool:
                            # Skip boolean fields in text search
                            continue
                        elif python_type == UUID:
                            # Try to parse as UUID if the search term matches a UUID format
                            if len(params.search) == 36:  # UUID length
                                try:
                                    uuid_val = UUID(params.search)
                                    search_conditions.append(column == uuid_val)
                                except ValueError:
                                    continue
                        elif python_type in (str, int, float):
                            # Use case-insensitive search for string fields
                            if python_type == str:
                                search_conditions.append(func.lower(column).like(f"%{params.search.lower()}%"))
                            # For numeric fields, try to convert and do exact match
                            elif python_type in (int, float):
                                try:
                                    numeric_val = python_type(params.search)
                                    search_conditions.append(column == numeric_val)
                                except ValueError:
                                    continue

                if search_conditions:
                    query = query.where(or_(*search_conditions))

            # Add filters if they exist
            if filters:
                query = self._apply_filters(query, filters)

            # Add deleted filter if it exists
            if not params.include_deleted:
                query = query.where(self.model.is_deleted.is_(False))

            # Add sort if it exists
            sort_field = params.sort_field or params.sort_by
            if sort_field:
                direction = desc if params.sort_direction == "desc" else asc
                query = query.order_by(direction(getattr(self.model, sort_field)))

            # Create a base query for counting that includes all the same conditions
            count_query = select(func.count()).select_from(query.subquery())
            total = await db_conn.scalar(count_query) or 0

            # Add limit if it exists
            if params.limit is not None:
                query = query.limit(params.limit)

            # Add offset if it exists
            if params.offset:
                query = query.offset(params.offset)

            # Execute query
            result = await db_conn.execute(query)
            items = result.unique().scalars().all()

            return FilterResponse[ModelType](  # Noqa
                items=items, # Noqa
                total=total,
                size=len(items)
            )

        except Exception:
            raise

    async def count(
            self,
            db_conn: AsyncSession,
            filters: Optional[List[FilterCondition]] = None,
            include_deleted: bool = False
    ) -> int:
        try:
            count_query = select(func.count()).select_from(self.model)

            if not include_deleted:
                count_query = count_query.filter(self.model.is_deleted.is_(False))

            if filters:
                count_query = self._apply_filters(count_query, filters)

            count = await db_conn.scalar(count_query)
            return count
        except Exception:
            raise

    def _apply_filters(self, query: Select, filters: List[FilterCondition]) -> Select:
        for filter_condition in filters:
            if not isinstance(filter_condition, FilterCondition):
                continue

            column = getattr(self.model, filter_condition.field, None)
            if not column:
                continue

            if filter_condition.type == "uuid":
                value = UUID(filter_condition.value)
            elif filter_condition.type == "int":
                value = int(filter_condition.value)
            elif filter_condition.type == "float":
                value = float(filter_condition.value)
            elif filter_condition.type == "bool":
                value = bool(filter_condition.value)
            elif filter_condition.type == "datetime":
                value = parse_sqlserver_datetime_aware(filter_condition.value)
            elif filter_condition.type == "date":
                value = datetime.strptime(filter_condition.value, "%Y-%m-%d").date()
            else:
                value = str(filter_condition.value)

            try:
                match filter_condition.operator:
                    case "eq":
                        query = query.where(column == value)  # noqa
                    case "neq":
                        query = query.where(column != value)  # noqa
                    case "gt":
                        query = query.where(column > value)  # noqa
                    case "lt":
                        query = query.where(column < value)  # noqa
                    case "gte":
                        query = query.where(column >= value)  # noqa
                    case "lte":
                        query = query.where(column <= value)  # noqa
                    case "like":
                        query = query.where(column.like(f"%{value}%"))
                    case "in":
                        query = query.where(column.in_(value))
                    case "not_in":
                        query = query.where(not_(column.in_(value)))
                    case "is_null":
                        query = query.where(column.is_(None))
                    case "is_not_null":
                        query = query.where(column.is_not(None))

            except (AttributeError, TypeError):
                continue
            except Exception:
                raise

        return query

    async def get_by_reference(
            self,
            db_conn: AsyncSession,
            reference_type: str,
            reference_name: str,
            reference_number: str,
            include_deleted: bool = False
    ) -> Optional[ModelType]:
        """Get a record by its reference type, name, and number.
        
        Args:
            db_conn: Database session
            reference_type: Type of reference (e.g., 'SILICA')
            reference_name: Name of the reference field (e.g., 'TRANSNO')
            reference_number: Value of the reference field
            include_deleted: Whether to include deleted records
            
        Returns:
            The model instance if found, None otherwise
        """
        try:
            query = (
                select(self.model)
                .where(
                    and_(
                        self.model.reference_type == reference_type,
                        self.model.reference_name == reference_name,
                        self.model.reference_number == reference_number
                    )
                )
            )

            if not include_deleted:
                query = query.where(self.model.is_deleted.is_(False))

            # Order by version in descending order to get the latest version
            query = query.order_by(desc(self.model.version))

            result = await db_conn.execute(query)
            return result.scalar_one_or_none()

        except Exception:
            raise

    async def get_all_hashes(
            self,
            db_conn: AsyncSession,
            reference_type: Optional[str] = None,
            reference_name: Optional[str] = None,
            reference_number: Optional[str] = None
    ) -> List[VersionSchema]:
        """Get all hash values, versions, and reference details from the model's table where hash is not null and status is not deleted
        
        Args:
            db_conn: Database session
            reference_type: Optional filter for reference_type
            reference_name: Optional filter for reference_name
            reference_number: Optional filter for reference_number
            
        Returns:
            List of VersionSchema objects containing hash, version, and reference details
        """
        try:
            # Build the base query
            query = (
                select(
                    self.model.hash,
                    self.model.version,
                    self.model.reference_number,
                    self.model.reference_type,
                    self.model.reference_name
                )
                .where(
                    and_(
                        self.model.hash.isnot(None),
                        self.model.status != 'deleted'
                    )
                )
            )

            # Add optional filters
            if reference_type:
                query = query.where(self.model.reference_type == reference_type)  # Noqa

            if reference_name:
                query = query.where(self.model.reference_name == reference_name)  # Noqa

            if reference_number:
                query = query.where(self.model.reference_number == reference_number)  # Noqa

            # Execute the query
            result = await db_conn.execute(query)
            rows = result.fetchall()

            # Convert to VersionSchema objects
            return [
                VersionSchema(
                    hash=row[0],
                    version=row[1],
                    reference_number=row[2] or "",
                    reference_type=row[3] or "",
                    reference_name=row[4] or ""
                )
                for row in rows
            ]

        except Exception:
            raise
