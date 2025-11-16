from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, Any, Optional, TypeVar, Type
from sqlalchemy import DateTime, Boolean, UUID, Index, Integer, String, select, desc, func, and_
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

T = TypeVar('T', bound='BaseModel')


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active"
    )

    reference_number: Mapped[Optional[str]] = mapped_column(
        String(255),
        default=None,
        nullable=True
    )

    reference_type: Mapped[Optional[str]] = mapped_column(
        String(255),
        default=None,
        nullable=True
    )

    reference_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        default=None,
        nullable=True
    )

    version: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=1,
        server_default="1"
    )

    hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True
    )

    @classmethod
    def get_highest_version(cls: Type[T], id_field_name, id_value, reference_number=None, reference_type=None,
                            reference_name=None):
        """
        Get the highest version of a record by its identifier field and reference parameters.
        
        Args:
            id_field_name: The name of the identifier field (e.g., 'client_number', 'account_number')
            id_value: The value of the identifier
            reference_number: Optional reference number to filter by
            reference_type: Optional reference type to filter by
            reference_name: Optional reference name to filter by
            
        Returns:
            Query that will return the highest version record when executed
        """
        id_field = getattr(cls, id_field_name)
        query = select(cls).where(
            and_(
                id_field == id_value,
                cls.is_deleted is False
            ))
        if reference_number is not None:
            query = query.filter(cls.reference_number == reference_number)
        if reference_type is not None:
            query = query.filter(cls.reference_type == reference_type)
        if reference_name is not None:
            query = query.filter(cls.reference_name == reference_name)
        return query.order_by(cls.version.desc()).limit(1)

    @classmethod
    def get_highest_version_collection(cls: Type[T], reference_number=None, reference_type=None, reference_name=None,
                                       offset=0, limit=100, order_by=None, additional_filters=None):
        """
        Get the highest version of each unique record in a collection.
        
        This method uses a window function to get only the highest version 
        of each record based on a unique identifier field.
        
        Args:
            reference_number: Optional reference number to filter by
            reference_type: Optional reference type to filter by  
            reference_name: Optional reference name to filter by
            offset: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field or expression to order results by
            additional_filters: Additional filter conditions to apply
            
        Returns:
            Query that will return the highest version of each record
        """
        # Get the unique identifier fields for this model
        partition_fields = cls.get_unique_identifier_fields()

        # Start with basic query filtering
        query = select(cls).where(cls.is_deleted is False)

        # Add reference filters if provided
        if reference_number is not None:
            query = query.filter(cls.reference_number == reference_number)
        if reference_type is not None:
            query = query.filter(cls.reference_type == reference_type)
        if reference_name is not None:
            query = query.filter(cls.reference_name == reference_name)

        # Apply additional filters if provided
        if additional_filters is not None:
            if isinstance(additional_filters, list):
                for filter_condition in additional_filters:
                    query = query.filter(filter_condition)
            else:
                query.filter(additional_filters)

        # Apply the window function to get the highest version of each unique record
        window_func = func.row_number().over(
            partition_by=partition_fields,
            order_by=desc(cls.version)
        ).label('row_number')

        # Create a subquery with row numbers
        subquery = select(cls, window_func).subquery()

        # Select only the rows with row_number = 1 (the highest version)
        query = select(cls).select_from(
            select(subquery).where(subquery.c.row_number == 1).subquery()  # Noqa
        )

        # Apply custom ordering if provided
        if order_by is not None:
            if isinstance(order_by, list):
                for order in order_by:
                    query = query.order_by(order)
            else:
                query = query.order_by(order_by)
        else:
            # Default ordering by created_at
            query = query.order_by(cls.created_at.desc())

        # Apply pagination if the limit is specified
        if limit is not None:
            query = query.limit(limit)

        # Apply offset if specified
        if offset is not None and offset > 0:
            query = query.offset(offset)

        return query

    @classmethod
    def get_unique_identifier_field(cls):
        """
        Returns the field that uniquely identifies records for version comparison.
        
        Subclasses should override this to specify which field is used
        to determine uniqueness for versioning.
        
        Deprecated: Use get_unique_identifier_fields instead.
        """
        raise NotImplementedError(
            "Subclasses must implement get_unique_identifier_field() or get_unique_identifier_fields()")

    @classmethod
    def get_unique_identifier_fields(cls):
        """
        Returns a list of fields that together uniquely identify records for version comparison.
        
        By default, this includes the business key field from get_unique_identifier_field() 
        plus reference_number, reference_type, and reference_name.
        
        Subclasses can override this for custom behavior.
        """
        try:
            # First, try to get the primary business key from the subclass
            primary_field = cls.get_unique_identifier_field()
            # Return a tuple of the primary field plus reference fields
            return primary_field, cls.reference_number, cls.reference_type, cls.reference_name
        except NotImplementedError:
            # If you get_unique_identifier_field is not implemented, just use reference fields
            return cls.reference_number, cls.reference_type, cls.reference_name

    @classmethod
    def __declare_last__(cls):
        if not cls.__abstract__:
            # super().__declare_last__()
            Index(f"idx_{cls.__tablename__}_status", "status", postgresql_using='hash',
                  info={'table_name': cls.__tablename__})
            Index(f"idx_{cls.__tablename__}_created_at", "created_at", postgresql_using='btree',
                  info={'table_name': cls.__tablename__})
            Index(f"idx_{cls.__tablename__}_hash", "hash", info={'table_name': cls.__tablename__})
            Index(f"idx_{cls.__tablename__}_version", "version", postgresql_using='hash',
                  info={'table_name': cls.__tablename__})
            Index(f"idx_{cls.__tablename__}_reference_number", "reference_number", postgresql_using='hash',
                  info={'table_name': cls.__tablename__})
            Index(f"idx_{cls.__tablename__}_reference_name", "reference_name", postgresql_using='hash',
                  info={'table_name': cls.__tablename__})
            Index(f"idx_{cls.__tablename__}_reference_type", "reference_type", postgresql_using='hash',
                  info={'table_name': cls.__tablename__})

    def to_dict(self) -> Dict[str, Any]:
        return {key: getattr(self, key) for key in self.__table__.columns.keys()}
