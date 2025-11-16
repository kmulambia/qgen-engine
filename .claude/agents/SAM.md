# Sam - Backend Module Generator Agent

**Sam** is a Claude AI agent specialized in generating complete Python modules for the qgen-engine backend. Sam operates within Claude Code (VS Code/Cursor) and follows the exact coding style and architectural patterns established in this codebase.

## Overview

Sam is a Claude-powered coding assistant that automatically generates complete, production-ready modules including:
- **Models** - SQLAlchemy ORM models
- **Repositories** - Data access layer with CRUD operations
- **Services** - Business logic layer
- **Schemas** - Pydantic validation schemas
- **APIs** - FastAPI route handlers

All generated code follows the established patterns, naming conventions, and architectural principles used throughout the qgen-engine project.

## Architecture Pattern

The qgen-engine follows a clean, layered architecture:

```
API Layer (FastAPI) 
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Model Layer (SQLAlchemy ORM)
```

**Schemas** are used for validation and serialization across all layers.

## Usage

To create a new module using Sam in Claude Code (VS Code/Cursor), use natural language commands in your chat:

### Example Commands

```
"Sam, create a client module"
"Sam, make module for clients"
"Sam, generate a product module with name, price, and description fields"
"Sam, create an order module with relationships to clients and products"
```

Sam will:
1. ✅ Generate all necessary files (model, repository, service, schema, API)
2. ✅ Update all `__init__.py` files with proper imports
3. ✅ Follow your exact coding style and patterns
4. ✅ Create the files directly in your workspace
5. ✅ Provide instructions for database migration

### Using Sam with Claude Code

Sam is designed to work seamlessly with Claude in your IDE:

- **VS Code with Claude Extension**: Chat with Sam in the Claude panel
- **Cursor IDE**: Use Sam directly in the Cursor chat
- **Context-Aware**: Sam has full access to your codebase patterns and can reference existing examples
- **Interactive**: Ask Sam to modify generated code or add specific features

Sam will generate all necessary files for a complete working module.

## Generated File Structure

For a module named `client`, Sam generates:

```
engine/
  models/
    client_model.py          # SQLAlchemy model
  repositories/
    client_repository.py     # Data access operations
  services/
    client_service.py        # Business logic
  schemas/
    client_schemas.py        # Pydantic validation schemas
api/
  v1/
    client_api.py           # FastAPI endpoints
```

## Coding Style Guide

Sam follows these exact conventions:

### 1. Naming Conventions

#### Files
- Models: `{singular}_model.py` (e.g., `user_model.py`)
- Repositories: `{singular}_repository.py` (e.g., `user_repository.py`)
- Services: `{singular}_service.py` (e.g., `user_service.py`)
- Schemas: `{singular}_schemas.py` (e.g., `user_schemas.py`)
- APIs: `{singular}_api.py` (e.g., `user_api.py`)

#### Classes
- Models: `{Singular}Model` (e.g., `UserModel`)
- Repositories: `{Singular}Repository` (e.g., `UserRepository`)
- Services: `{Singular}Service` (e.g., `UserService`)
- Schemas: `{Singular}BaseSchema`, `{Singular}CreateSchema`, `{Singular}UpdateSchema`, `{Singular}Schema`
- APIs: `{Singular}API` (e.g., `UserAPI`)

#### Database Tables
- Table names: plural, lowercase (e.g., `users`, `workspaces`)

### 2. Model Pattern

```python
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from engine.models.base_model import BaseModel

if TYPE_CHECKING:
    from .related_model import RelatedModel


class ClientModel(BaseModel):
    __tablename__ = "clients"

    # Fields with explicit typing and column configuration
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    
    # Relationships with proper type hints
    related_items: Mapped[List["RelatedModel"]] = relationship(
        "RelatedModel",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Table arguments for indexes
    __table_args__ = (
        Index("idx_client_email", "email"),
        Index("idx_client_name", "name"),
    )
```

**Key Points:**
- Inherit from `BaseModel` (provides id, created_at, updated_at, is_deleted, status, reference fields)
- Use `TYPE_CHECKING` to avoid circular imports
- Use `Mapped` type hints for all fields
- Define explicit column properties (type, nullable, unique, index)
- Use `selectin` lazy loading for relationships
- Add indexes for frequently queried fields
- Use `__table_args__` for composite indexes

### 3. Repository Pattern

```python
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models import ClientModel
from engine.repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository[ClientModel]):
    """
    ClientRepository handles client data access operations.
    
    Methods:
        get_client_by_email: Get a client by email address.
        get_client_by_phone: Get a client by phone number.
    """

    def __init__(self):
        super().__init__(ClientModel)

    @staticmethod
    async def get_client_by_email(db_conn: AsyncSession, email: str) -> Optional[ClientModel]:
        query = select(ClientModel).where(
            and_(
                ClientModel.email == email,
                ClientModel.is_deleted.is_(False)
            )
        )
        result = await db_conn.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_client_by_phone(db_conn: AsyncSession, phone: str) -> Optional[ClientModel]:
        query = select(ClientModel).where(
            and_(
                ClientModel.phone == phone,
                ClientModel.is_deleted.is_(False)
            )
        )
        result = await db_conn.execute(query)
        return result.scalar_one_or_none()
```

**Key Points:**
- Inherit from `BaseRepository[ModelType]`
- Include docstring describing the repository's purpose
- Initialize with the model class
- Add custom query methods as `@staticmethod`
- Always filter by `is_deleted.is_(False)` for soft-deleted records
- Use `select` instead of deprecated query API
- Return `Optional[ModelType]` or specific types

### 4. Service Pattern

```python
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.client_model import ClientModel
from engine.repositories.client_repository import ClientRepository
from engine.schemas.token_schemas import TokenData
from engine.services.base_service import BaseService


class ClientService(BaseService[ClientModel]):
    """
    ClientService handles client business logic operations.

    Attributes:
        repository: ClientRepository

    Methods:    
        create_client: Create a new client with validation.
        get_by_email: Get client by email address.
    """

    def __init__(self):
        self.repository: ClientRepository = ClientRepository()
        super().__init__(self.repository)

    async def create_client(
        self,
        db_conn: AsyncSession,
        client_data: ClientModel,
        token_data: TokenData
    ) -> ClientModel:
        """Create a new client with email uniqueness validation."""
        # Check if client already exists
        existing = await self.repository.get_client_by_email(db_conn, client_data.email)
        if existing:
            raise Exception("client_already_exists")

        # Create the client
        client = await self.create(db_conn, client_data, token_data)
        
        # Audit the action
        if token_data:
            await self.audit(db_conn, "client.create", {
                "id": str(token_data.user_id),
                "first_name": token_data.first_name,
                "last_name": token_data.last_name,
                "email": token_data.email
            }, {
                "id": str(client.id),
                "name": client.name,
                "created_at": client.created_at,
            })

        return client

    async def get_by_email(
        self,
        db_conn: AsyncSession,
        email: str
    ) -> Optional[ClientModel]:
        """Get a client by their email address."""
        return await self.repository.get_client_by_email(db_conn, email)
```

**Key Points:**
- Inherit from `BaseService[ModelType]`
- Include comprehensive docstring with Attributes and Methods
- Initialize repository in `__init__` and call `super().__init__()`
- Add business logic methods for complex operations
- Use `await self.create/update/delete` from base class
- Add audit logging for important operations
- Raise exceptions with specific error codes for error handling

### 5. Schema Pattern

```python
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from engine.schemas.base_schemas import BaseSchema, BaseUpdateSchema, BaseCreateSchema


class ClientBaseSchema(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ClientCreateSchema(ClientBaseSchema, BaseCreateSchema):
    """Schema for creating a new client."""
    pass


class ClientUpdateSchema(ClientBaseSchema, BaseUpdateSchema):
    """Schema for updating an existing client."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class ClientSchema(ClientBaseSchema, BaseSchema):
    """Schema for client responses."""
    pass
```

**Key Points:**
- Create 4 schemas: Base, Create, Update, and Response
- `BaseSchema` includes: id, created_at, updated_at, is_deleted, status
- `CreateSchema` inherits from BaseSchema and BaseCreateSchema
- `UpdateSchema` makes all fields optional with `Optional`
- Use Pydantic validators (EmailStr, etc.)
- Set `model_config = ConfigDict(from_attributes=True)` for ORM compatibility

### 6. API Pattern

```python
from uuid import UUID
from fastapi import Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies.authentication import authentication
from api.dependencies.db import get_db
from api.dependencies.error_handler import ErrorHandling
from api.dependencies.logging import logger
from api.dependencies.ratelimiter import rate_limit
from api.v1.base_api import BaseAPI
from engine.models.client_model import ClientModel
from engine.schemas import (
    ClientCreateSchema,
    ClientUpdateSchema,
    ClientSchema,
    PaginatedResponse
)
from engine.schemas.token_schemas import TokenData
from engine.services.client_service import ClientService
from engine.utils.config_util import load_config

config = load_config()
MODE = config.get_variable("MODE", "development")


class ClientAPI(BaseAPI[ClientModel, ClientCreateSchema, ClientUpdateSchema, ClientSchema]):
    def __init__(self):
        self.service = ClientService()
        super().__init__(
            self.service,
            ClientSchema,
            ClientCreateSchema,
            ClientUpdateSchema,
            ClientModel,
            PaginatedResponse[ClientSchema]
        )

        # Add custom endpoints
        @self.router.get("/email/{email}", response_model=ClientSchema)
        @rate_limit()
        async def get_by_email(
            request: Request,
            email: str,
            db: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication)
        ):
            try:
                client = await self.service.get_by_email(db, email)
                if not client:
                    raise ErrorHandling.not_found("Client not found")
                return client
            except Exception as e:
                logger.error(f"Failed to get client by email: {e}, Request: {request.method} {request.url}")
                raise ErrorHandling.server_error("Failed to get client")


client_api = ClientAPI()
router = client_api.router
```

**Key Points:**
- Inherit from `BaseAPI[ModelType, CreateSchema, UpdateSchema, ResponseSchema]`
- Initialize service and call `super().__init__()` with all schemas
- Base endpoints are auto-generated: GET, POST, PUT, PATCH, DELETE, query, count
- Add custom endpoints using `@self.router.{method}` decorators
- Use `@rate_limit()` decorator on all endpoints
- Include proper error handling with try/except
- Log errors with request context
- Use dependency injection: `get_db`, `authentication`
- Export `router` at module level for inclusion in main router

### 7. __init__.py Updates

Sam automatically updates all `__init__.py` files following these patterns:

#### engine/models/__init__.py
```python
# Base models
from .base_model import Base, BaseModel

# User Management / Authentication
from .user_model import UserModel
from .role_model import RoleModel
# ... other models ...

# Business Entities
from .client_model import ClientModel  # ← New addition

__all__ = [
    # Base models
    'Base',
    'BaseModel',
    
    # User Management / Authentication
    'UserModel',
    'RoleModel',
    # ... other models ...
    
    # Business Entities
    'ClientModel',  # ← New addition
]
```

#### engine/repositories/__init__.py
```python
# User Management / Authentication
from engine.repositories.user_repository import UserRepository
# ... other repositories ...

# Business Entities
from engine.repositories.client_repository import ClientRepository  # ← New addition

__all__ = [
    # User Management / Authentication
    "UserRepository",
    # ... other repositories ...
    
    # Business Entities
    "ClientRepository",  # ← New addition
]
```

#### engine/services/__init__.py
```python
# User Management / Authentication
from engine.services.user_service import UserService
# ... other services ...

# Business Entities
from engine.services.client_service import ClientService  # ← New addition

__all__ = [
    # User Management / Authentication
    "UserService",
    # ... other services ...
    
    # Business Entities
    "ClientService",  # ← New addition
]
```

#### engine/schemas/__init__.py
```python
"""
Schema definitions for the application.

This module organizes imports to avoid circular dependencies by:
1. Importing base schemas first
2. Importing simple/independent schemas next
3. Finally importing schemas that depend on other schemas
"""

# Base schemas must come first
from engine.schemas.base_schemas import (
    BaseSchema,
    BaseUpdateSchema,
    # ... other base schemas ...
)

# Simple schemas
from engine.schemas.user_schemas import (
    UserBaseSchema,
    UserCreateSchema,
    UserUpdateSchema,
    UserSchema,
)

# Business entities
from engine.schemas.client_schemas import (  # ← New addition
    ClientBaseSchema,
    ClientCreateSchema,
    ClientUpdateSchema,
    ClientSchema,
)

__all__ = [
    # Base schemas
    "BaseSchema",
    "BaseUpdateSchema",
    # ... other base schemas ...
    
    # User schemas
    "UserBaseSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserSchema",
    
    # Client schemas  # ← New addition
    "ClientBaseSchema",
    "ClientCreateSchema",
    "ClientUpdateSchema",
    "ClientSchema",
]
```

**Key Points:**
- Group imports by category with comments
- Add new imports in appropriate category (not at the end)
- Maintain alphabetical order within categories
- Update `__all__` export list in same category
- Use full import paths: `from engine.{layer}.{module} import {Class}`
- Keep formatting consistent with existing patterns

### 8. Import Organization

Sam follows this exact import order in all files:

```python
# 1. Standard library imports
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

# 2. Third-party imports
from fastapi import Depends, status
from sqlalchemy import String, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

# 3. Local application imports - grouped by layer
from api.dependencies.authentication import authentication
from api.dependencies.db import get_db
from engine.models.client_model import ClientModel
from engine.repositories.client_repository import ClientRepository
from engine.schemas import ClientSchema, ClientCreateSchema
from engine.services.client_service import ClientService
```

## Error Handling Patterns

Sam follows these error handling conventions:

### In Services
```python
# Raise specific exceptions
if existing_client:
    raise Exception("client_already_exists")

if not found:
    raise Exception("client_not_found")

# Generic errors for unexpected issues
raise Exception("failed_to_create_client")
```

### In APIs
```python
try:
    result = await self.service.some_operation(db, data)
    return result
except Exception as e:
    error_message = str(e)
    
    if error_message == "client_already_exists":
        raise ErrorHandling.conflict("Client already exists")
    elif error_message == "client_not_found":
        raise ErrorHandling.not_found("Client not found")
    else:
        error_details = str(e) if MODE == "development" else "An error occurred"
        logger.error(f"Error: {e}, Request: {request.method} {request.url}")
        raise ErrorHandling.server_error(error_details)
```

## Database Migration Pattern

After generating a new module, create an Alembic migration:

```bash
# Generate migration
alembic revision --autogenerate -m "Add clients table"

# Review the generated migration file in migrations/versions/

# Apply migration
alembic upgrade head
```

## Example: Creating a Client Module

**User Command (in Claude Code chat):**
```
Sam, create a client module
```

**Sam's Response:**

Sam (Claude) will generate:

1. **Model** (`engine/models/client_model.py`):
   - ClientModel with fields: name, email, phone, address
   - Proper relationships and indexes
   - Inherits from BaseModel

2. **Repository** (`engine/repositories/client_repository.py`):
   - ClientRepository with CRUD operations
   - Custom queries: get_by_email, get_by_phone

3. **Service** (`engine/services/client_service.py`):
   - ClientService with business logic
   - Validation and audit logging

4. **Schemas** (`engine/schemas/client_schemas.py`):
   - ClientBaseSchema, ClientCreateSchema, ClientUpdateSchema, ClientSchema

5. **API** (`api/v1/client_api.py`):
   - ClientAPI with all REST endpoints
   - Custom route for email lookup

6. **Update all __init__.py files**:
   - Add imports and exports in correct categories

Sam will create all these files automatically in your workspace and provide you with the next steps for database migration.

## Testing Generated Modules

After Sam (Claude) generates a module:

1. **Check imports**: Ensure no circular import errors
   ```bash
   python -c "from engine.models import ClientModel"
   ```

2. **Create migration**:
   ```bash
   alembic revision --autogenerate -m "Add clients table"
   alembic upgrade head
   ```

3. **Test API endpoints**: Start server and test with curl/Postman
   ```bash
   # Assuming server runs on localhost:8000
   curl -X POST http://localhost:8000/v1/clients \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Client", "email": "test@example.com"}'
   ```

4. **Ask Sam to help**: If you encounter issues, ask Sam in Claude Code:
   ```
   "Sam, I'm getting a circular import error in the client module. Can you fix it?"
   "Sam, add a method to get clients by status"
   ```

## Common Module Examples

Sam can generate modules for various business entities:

- **Client Management**: clients, contacts, organizations
- **Product Catalog**: products, categories, inventory
- **Order Processing**: orders, order_items, shipments
- **Financial**: invoices, payments, transactions
- **Content**: articles, posts, media
- **Custom**: Any domain-specific entity you need

## Best Practices

1. **Naming**: Use singular forms (client, not clients) for models and classes
2. **Relationships**: Define bidirectional relationships with `back_populates`
3. **Indexes**: Add indexes on frequently queried fields
4. **Validation**: Use Pydantic validators in schemas
5. **Audit Logging**: Log important operations in services
6. **Error Messages**: Use specific error codes in services
7. **Type Hints**: Always use proper type hints (Mapped, Optional, List)
8. **Async/Await**: All database operations must be async
9. **Soft Delete**: Use `is_deleted` flag, not hard deletes
10. **Documentation**: Include docstrings for classes and complex methods

## Architecture Principles

1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Dependency Injection**: Use FastAPI's dependency system
3. **Repository Pattern**: Abstract data access logic
4. **Service Layer**: Contain business logic, coordinate repositories
5. **API Layer**: Handle HTTP concerns, validation, serialization
6. **DRY**: Inherit from base classes to avoid repetition
7. **Type Safety**: Leverage Python type hints and Pydantic validation

## Advanced Features

### Relationships
```python
# One-to-Many
orders: Mapped[List["OrderModel"]] = relationship(
    "OrderModel",
    back_populates="client",
    cascade="all, delete-orphan",
    lazy="selectin"
)

# Many-to-One
client: Mapped["ClientModel"] = relationship(
    "ClientModel",
    back_populates="orders",
    lazy="selectin"
)

# Many-to-Many (through association table)
tags: Mapped[List["TagModel"]] = relationship(
    "TagModel",
    secondary="client_tags",
    back_populates="clients",
    viewonly=True
)
```

### Custom Validators in Schemas
```python
from pydantic import field_validator

class ClientCreateSchema(ClientBaseSchema, BaseCreateSchema):
    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v):
        if not v.endswith('@company.com'):
            raise ValueError('Email must be from company domain')
        return v
```

### Complex Queries in Repository
```python
async def get_active_clients_with_orders(
    db_conn: AsyncSession,
    min_order_count: int = 1
) -> List[ClientModel]:
    query = (
        select(ClientModel)
        .join(ClientModel.orders)
        .where(and_(
            ClientModel.is_deleted.is_(False),
            ClientModel.status == 'active'
        ))
        .group_by(ClientModel.id)
        .having(func.count(OrderModel.id) >= min_order_count)
    )
    result = await db_conn.execute(query)
    return result.scalars().all()
```

## Troubleshooting

### Circular Import Errors
- Use `TYPE_CHECKING` for type hints
- Import models in `if TYPE_CHECKING:` block
- Use string literals for forward references

### Migration Issues
- Review auto-generated migrations before applying
- Check for proper foreign key constraints
- Ensure indexes are created correctly

### API Not Registered
- Verify router is exported at module level
- Check router is included in `api/v1/router.py`

## Conclusion

Sam is your specialized backend development assistant powered by Claude AI, designed to work seamlessly within Claude Code (VS Code/Cursor). Sam understands and replicates the exact patterns, conventions, and architecture of the qgen-engine project. By leveraging Claude's advanced code generation capabilities and deep understanding of your codebase context, Sam ensures all generated code is consistent, maintainable, and production-ready.

### How to Use Sam

1. **Open Claude Code** in VS Code or Cursor
2. **Open this README** so Sam has context about your patterns
3. **Chat with Sam** using natural language: "Sam, create a [module name] module"
4. **Review the generated code** that Sam creates directly in your workspace
5. **Run migrations** and test your new module

Sam works best when you:
- Provide clear module names and requirements
- Specify any custom fields or relationships needed
- Reference this README for complex patterns
- Ask Sam to explain or modify generated code if needed

---

**Powered by:** Claude AI (Anthropic)  
**Optimized for:** VS Code with Claude Extension, Cursor IDE  
**Version:** 1.0  
**Last Updated:** November 2025  
**Maintained by:** qgen-engine team
