from datetime import datetime
from enum import Enum
from typing import Optional, Generic, List, TypeVar, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')

base_config = ConfigDict(
    from_attributes=True,
    extra="ignore",
    validate_assignment=True,
    # Add configuration to handle SQLAlchemy objects safely
    arbitrary_types_allowed=True,
    json_encoders={
        datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
    }
)


class VersionSchema(BaseModel):
    hash: str
    version: int
    reference_number: str
    reference_type: str
    reference_name: str


# Base Schema for all models
class BaseSchema(BaseModel):
    """
    A base schema for all models
    """
    id: Optional[UUID] = None
    version: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[str] = "active"
    is_deleted: Optional[bool] = False

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        # Add extra configuration to be more defensive
        extra="ignore",
        # Add configuration to handle SQLAlchemy objects safely
        validate_assignment=True
    )


class BaseCreateSchema(BaseModel):
    pass


class BaseUpdateSchema(BaseModel):
    updated_at: datetime = Field(default_factory=datetime.now)
    status: Optional[str] = Field(default="active")
    is_deleted: Optional[bool] = Field(default=False)


# Filtering and Sorting
class FilterOperator(str, Enum):
    """Filter operators for query conditions"""
    EQ = "eq"  # equals
    NEQ = "neq"  # not equals
    GT = "gt"  # greater than
    LT = "lt"  # less than
    GTE = "gte"  # greater than or equal
    LTE = "lte"  # less than or equal
    LIKE = "like"  # LIKE query
    IN = "in"  # IN query
    NOT_IN = "not_in"  # NOT IN query
    IS_NULL = "is_null"  # IS NULL
    IS_NOT_NULL = "is_not_null"  # IS NOT NULL


class FilterCondition(BaseModel):
    """Filter condition for queries"""
    field: str
    operator: FilterOperator
    value: Any
    type: Optional[str] = None


class FilterParams(BaseModel):
    """Parameters for sorting and filtering"""
    search: Optional[str] = None
    limit: Optional[int] = Field(default=1000, gt=0)
    offset: Optional[int] = Field(default=0)
    sort_by: Optional[str] = None
    sort_field: str = Field(default="created_at")
    sort_direction: str = Field(default="desc", pattern="^(asc|desc)$")
    include_deleted: bool = Field(default=False)
    versioned: Optional[bool] = Field(default=False)

    model_config = base_config


class FilterResponse(BaseModel, Generic[T]):
    """Enhanced pagination response with additional metadata"""
    items: List[T]
    total: int
    size: int

    model_config = base_config


# API Filtering and Sorting
class PaginationParams(BaseModel):
    """Parameters for pagination and sorting"""
    search: Optional[str] = None
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=10, gt=0)
    sort_by: Optional[str] = None
    size: int = Field(default=10, gt=0)
    sort_field: str = Field(default="")
    sort_direction: str = Field(default="asc", pattern="^(asc|desc)$")
    include_deleted: bool = False

    model_config = base_config


class PaginatedResponse(BaseModel, Generic[T]):
    """Enhanced pagination response with additional metadata"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

    model_config = base_config

    @property
    def next_page(self) -> Optional[int]:
        """Returns the next page number if available, else None"""
        return self.page + 1 if self.has_next else None

    @property
    def prev_page(self) -> Optional[int]:
        """Returns the previous page number if available, else None"""
        return self.page - 1 if self.has_prev else None


class CountResponse(BaseModel):
    """Response for count queries"""
    count: int

    model_config = base_config
