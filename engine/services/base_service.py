import datetime
from typing import Any, Dict, Generic, TypeVar, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models import AuditModel
from engine.schemas.token_schemas import TokenData
from engine.repositories.base_repository import BaseRepository
from engine.schemas.base_schemas import FilterCondition, FilterResponse, FilterParams, FilterOperator, VersionSchema
from engine.repositories.audit_repository import AuditRepository
from engine.utils.json_utils import to_json
from datetime import datetime, timezone

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """
    Base service class that provides CRUD operations using a repository  

    Attributes:
            repository: Repository instance
            audit_repository: Audit repository instance
            service_name: Name of the service

        Methods:
            create: Create a new record
            update: Update an existing record
            delete: Delete a record
            get_by_id: Get a record by id
            get_all: Get all records
            count: Count records
            audit: Create an audit log entry
    """

    def __init__(
            self,
            repository: BaseRepository[ModelType],
    ):
        self.repository = repository
        self.audit_repository = AuditRepository()
        self.service_name = self.__class__.__name__.replace('Service', '').lower()

    async def create(
            self,
            db_conn: AsyncSession,
            data: ModelType,
            token_data: Optional[TokenData] = None  # noqa
    ) -> ModelType:
        try:
            """
            Create a new record
            :param db_conn:
            :param data:
            :param token_data:
            :return:
            """
            # TODO : add validating data check
            result = await self.repository.create(db_conn, data)
            if token_data:
                await self.audit(db_conn, f"{self.service_name}.create",
                                 {
                                     "id": str(token_data.user_id),
                                     "first_name": token_data.first_name,
                                     "last_name": token_data.last_name,
                                     "email": token_data.email
                                 },
                                 entity_metadata={
                                     "id": str(result.id),
                                     "created_at": result.created_at
                                 })
            return result
        except Exception:
            raise

    async def update(
            self,
            db_conn: AsyncSession,
            uid: UUID,
            data: ModelType,
            token_data: Optional[TokenData] = None  # noqa
    ) -> Optional[ModelType]:
        """
        Update an existing record
        :param db_conn:
        :param uid:
        :param data:
        :param token_data:
        :return:
        """
        try:
            result = await self.repository.update(db_conn, uid, data)
            if token_data:
                await self.audit(db_conn, f"{self.service_name}.update",
                                 {
                                     "id": str(token_data.user_id),
                                     "first_name": token_data.first_name,
                                     "last_name": token_data.last_name,
                                     "email": token_data.email
                                 },
                                 entity_metadata={
                                     "id": str(result.id),
                                     "updated_at": result.updated_at,
                                     "status": result.status
                                 })
            return result
        except Exception:
            raise

    async def delete(
            self,
            db_conn: AsyncSession,
            uid: UUID,
            hard_delete: bool = False,
            token_data: Optional[TokenData] = None  # noqa
    ) -> bool:
        """
        Delete a record
        :param db_conn:
        :param uid:
        :param hard_delete:
        :param token_data:
        :return:
        """
        try:
            result = await self.repository.delete(db_conn, uid, hard_delete)
            if token_data:
                await self.audit(db_conn, f"{self.service_name}.delete",
                                 {
                                     "id": str(token_data.user_id),
                                     "first_name": token_data.first_name,
                                     "last_name": token_data.last_name,
                                     "email": token_data.email
                                 }, entity_metadata={
                        "id": str(uid),
                        "hard_delete": hard_delete
                    })
            return result
        except Exception:
            raise

    async def get_by_id(self, db_conn: AsyncSession, uid: UUID) -> Optional[ModelType]:
        """Get a record by its id

        Args:
            db_conn: Database session
            uid: UUID of the record

        Returns:        
            The model instance if found, None otherwise
        """
        try:
            return await self.repository.get_by_id(db_conn, uid)
        except Exception:
            raise

    async def get_all(
            self,
            db_conn: AsyncSession,
            params: Optional[FilterParams] = None,
            filters: Optional[List[FilterCondition]] = None,
            token_data: Optional[TokenData] = None  # noqa
    ) -> FilterResponse[ModelType]:
        """
        Get all records with optional filters and pagination
        :param db_conn:
        :param params:
        :param filters:
        :param token_data:
        :return:
        """
        try:
            result = await self.repository.get_all(db_conn=db_conn, params=params, filters=filters)
            return result
        except Exception:
            raise

    async def count(
            self,
            db_conn: AsyncSession,
            filters: Optional[List[FilterCondition]] = None,
            include_deleted: bool = False,
            token_data: Optional[TokenData] = None  # noqa
    ) -> int:
        return await self.repository.count(db_conn=db_conn, filters=filters, include_deleted=include_deleted)

    async def get_all_hashes(self, db: AsyncSession, reference_type: Optional[str] = None,
                             reference_name: Optional[str] = None, reference_number: Optional[str] = None) -> List[VersionSchema]:
        """Get all hash values, versions, and reference numbers from the model's table where hash is not null and status is not deleted
        
        Args:
            db: Database session
            reference_type: Optional filter for reference_type
            reference_name: Optional filter for reference_name
            reference_number: Optional filter for reference_number
            
        Returns:
            List of VersionSchema objects containing hash, version, reference_number, reference_type, and reference_name
        """
        try:
            return await self.repository.get_all_hashes(
                db_conn=db,
                reference_type=reference_type,
                reference_name=reference_name,
                reference_number=reference_number
            )
        except Exception:
            raise

    async def get_by_hash(self, db: AsyncSession, hash_value: str) -> Optional[ModelType]:
        """Get a record by its hash value

        Args:
            db: Database session
            hash_value: Hash value to search for

        Returns:
            The model instance if found, None otherwise
        """
        try:
            filters = [FilterCondition(field="hash", operator=FilterOperator.EQ, value=hash_value)]
            result = await self.repository.get_all(db, FilterParams(limit=1), filters=filters)
            return result.items[0] if result.items else None
        except Exception:
            raise

    async def get_by_reference(
            self,
            db_conn: AsyncSession,
            reference_type: str,
            reference_name: str,
            reference_number: str,
            include_deleted: bool = False,
            token_data: Optional[TokenData] = None  # noqa
    ) -> Optional[ModelType]:
        """Get a record by its reference type, name, and number.
        
        Args:
            db_conn: Database session
            reference_type: Type of reference (e.g., 'SILICA')
            reference_name: Name of the reference field (e.g., 'TRANSNO')
            reference_number: Value of the reference field
            include_deleted: Whether to include deleted records
            token_data: Optional token data for auditing
            
        Returns:
            The model instance if found, None otherwise
        """
        try:
            result = await self.repository.get_by_reference(
                db_conn,
                reference_type,
                reference_name,
                reference_number,
                include_deleted
            )

            if token_data and result:
                await self.audit(
                    db_conn,
                    f"{self.service_name}.get_by_reference",
                    {
                        "id": str(token_data.user_id),
                        "first_name": token_data.first_name,
                        "last_name": token_data.last_name,
                        "email": token_data.email
                    },
                    entity_metadata={
                        "reference_type": reference_type,
                        "reference_name": reference_name,
                        "reference_number": reference_number
                    }
                )

            return result

        except Exception:
            raise

    async def bulk_create(self, db_conn: AsyncSession, data: List[ModelType]) -> Dict[str, Any]:
        """Bulk create records with individual success/failure tracking

        Args:
            db_conn: Database session
            data: List of model instances to create

        Returns:
            Dictionary containing successful and failed records
        """
        try:
            return await self.repository.bulk_create(db_conn, data)
        except Exception:
            raise

    async def audit(
            self,
            db_conn: AsyncSession,
            action: str,
            user: Optional[Dict[str, Any]] = None,
            entity_metadata: Optional[dict] = None,
            status: str = 'success',
    ) -> AuditModel:
        """
            Create an audit log entry

            Args:
                db_conn: Database session
                action: The action being audited (e.g. "user.create")
                user: Dictionary containing user-specific metadata
                entity_metadata: Dictionary containing entity-specific metadata
                status: Status of the action (default: 'success')

            Returns:
                AuditModel: The audit log entry
            """
        try:
            audit_data = AuditModel(
                action=action,
                user_id=UUID(user["id"]) if user and isinstance(user, dict) and "id" in user else None,
                user_metadata=to_json(user) if user else None,
                entity_metadata=to_json(entity_metadata) if entity_metadata else None,
                status=status,
                created_at=datetime.now(timezone.utc)
            )
            # Use auto_commit=False to let the parent transaction handle the commit
            return await self.audit_repository.create(db_conn, audit_data)
        except Exception:
            raise
