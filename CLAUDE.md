# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Amphibia Engine** is the core service engine for the Umodzi Source platform, providing essential functionality including database management, authentication, email services, and RESTful API endpoints. It's a FastAPI-based backend with a clean layered architecture.

## Common Commands

### Running Services

```bash
# Run the main FastAPI application (from api/__init__.py)
python -m api
# or with uvicorn directly (with auto-reload)
uvicorn api:app --reload

# Run the mailer service (message queue consumer)
python -m mailer

# Run the seeder service (database initialization)
python -m seeder
```

### Development

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Database Management

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current migration status
alembic current

# View migration history
alembic history
```

### Seeder Operations

The seeder provides an interactive menu with options:
1. **Seed Data Only**: Runs all seeders (permissions, roles, workspace types)
2. **Truncate Tables and Reseed**: Clears all data and reseeds
3. **Rebuild Tables and Seed**: Drops and recreates all tables, then seeds
4. **Create Super User**: Creates a new super admin user

## Architecture

### Layered Architecture

The codebase follows a strict 4-layer architecture pattern:

**API Layer** (`api/`) → **Service Layer** (`engine/services/`) → **Repository Layer** (`engine/repositories/`) → **Model Layer** (`engine/models/`)

- **API Layer**: FastAPI routers handling HTTP requests, authentication, rate limiting, and response serialization
- **Service Layer**: Business logic, orchestration, and auditing
- **Repository Layer**: Database queries using SQLAlchemy async patterns
- **Model Layer**: SQLAlchemy ORM models with versioning and soft-delete support

### Base Classes Pattern

All entities inherit from base classes that provide common functionality:

#### BaseModel (`engine/models/base_model.py`)
All database models inherit from `BaseModel`, which provides:
- **Standard fields**: `id` (UUID), `created_at`, `updated_at`, `is_deleted`, `status`
- **Versioning fields**: `reference_number`, `reference_type`, `reference_name`, `version`, `hash`
- **Soft delete support**: Use `is_deleted` flag instead of hard deletes
- **Versioning methods**: `get_highest_version()`, `get_highest_version_collection()`, `get_unique_identifier_field()`

When creating new models, you must:
1. Inherit from `BaseModel`
2. Define a `__tablename__`
3. Implement `get_unique_identifier_field()` if using versioning

#### BaseRepository (`engine/repositories/base_repository.py`)
Generic repository providing CRUD operations:
- `create()`, `update()`, `delete()` (soft delete by default)
- `get_by_id()`, `get_all()`, `count()`
- `get_by_reference()`, `get_all_hashes()` (for versioning)
- `bulk_create()` with individual success/failure tracking
- Advanced filtering with `FilterCondition` and `FilterParams`
- Automatic relationship loading with `selectinload`

#### BaseService (`engine/services/base_service.py`)
Generic service layer providing:
- CRUD operations with automatic auditing
- `audit()` method for creating audit logs
- Integrates with `TokenData` for user context
- Error handling and transaction management

#### BaseAPI (`api/v1/base_api.py`)
Generic API router providing standard REST endpoints:
- `POST /` - Create item
- `GET /{uid}` - Get item by ID
- `PUT /{uid}` - Update item
- `GET /` - List items with pagination
- `POST /query` - Query items with filters
- `POST /count` - Count items
- `DELETE /{uid}` - Delete item (soft/hard)

All endpoints include:
- JWT authentication via Bearer token
- Rate limiting
- Automatic relationship loading
- Validation error fallback handling

### Key Components

#### Authentication Flow
1. User credentials validated via `api/v1/auth_api.py`
2. JWT tokens issued by `engine/services/token_service.py`
3. Tokens stored in database (`engine/models/token_model.py`)
4. Authentication middleware (`api/dependencies/authentication.py`) validates tokens on protected routes
5. `TokenData` object passed to services containing user context (user_id, first_name, last_name, email, roles, permissions)

**Protected endpoints** use `authentication` dependency:
```python
from api.dependencies.authentication import authentication
from engine.schemas.token_schemas import TokenData

@router.get("/protected")
async def protected_route(
    token_data: TokenData = Depends(authentication)
):
    # token_data contains user information
    user_id = token_data.user_id
    permissions = token_data.permissions
```

#### Database Connections
- Primary PostgreSQL connection via `PostgresDataSource` (`engine/datasources/postgres_ds.py`)
- Async SQLAlchemy with asyncpg driver
- Connection pooling configured with pool_size=10, max_overflow=20
- Redis cache for session management (`engine/datasources/redis_ds.py`)

#### Message Queue Integration
- Uses `aio-pika` for RabbitMQ integration
- Mailer service consumes from AMQ queue
- Configured via `AMQ_URI`, `AMQ_QUEUE_NAME`, `AMQ_EMAIL_SERVICE` environment variables
- Middleware at `engine/middleware/amq_middleware.py`

#### Configuration Management
Environment variables loaded via `dotenv` using the `EnvConfig` class at `engine/utils/config_util.py`.

**Usage pattern**:
```python
from engine.utils.config_util import load_config

config = load_config()  # Cached via @lru_cache

# Get optional variable with default
mode = config.get_variable("MODE", default="development")

# Get required variable (raises EnvConfigError if missing)
port = config.require_variable("PORT", cast_type=int)

# Automatic type casting
debug = config.get_variable("DEBUG", cast_type=bool)  # Handles "true", "1", "yes", "on"
cors = config.get_variable("CORS_ORIGINS", cast_type=list)  # Splits by comma
```

**Required environment variables**:
- Application: `HOST`, `PORT`, `NAME`, `DESCRIPTION`, `VERSION`, `MODE`
- Database: `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
- JWT: `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRATION_MINUTES`
- Rate limiting: `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW`
- Email: `POSTMARK_API_TOKEN`, `EMAIL` (sender address)
- Message Queue: `AMQ_URI`, `AMQ_QUEUE_NAME`, `AMQ_EMAIL_SERVICE`

#### Seeding System
Configuration-driven seeding from JSON files in `config/`:
- `permissions.json` - Application permissions
- `roles.json` - User roles
- `workspace_types.json` - Workspace type definitions
- `workspaces.json` - Initial workspaces

Seeders run in sequence:
1. Permission seeder
2. Role seeder
3. Workspace type seeder
4. Workspace seeder
5. User seeder (interactive for super admin creation)

### API Versioning & Extension
All API routes are versioned under `/api/v1/*`. To add new endpoints:
1. Create API class inheriting from `BaseAPI` (or `APIRouter` for custom endpoints)
2. Register router in `api/v1/router.py`
3. Add appropriate tags for OpenAPI documentation

**Extending BaseAPI**: You can override base routes by removing them and adding custom implementations:
```python
class UserAPI(BaseAPI[UserModel, UserCreateSchema, UserUpdateSchema, UserSchema]):
    def __init__(self):
        super().__init__(...)

        # Remove default routes
        routes_to_remove = [
            route for route in self.router.routes
            if route.path == "" and route.methods == {"POST"}
        ]
        for route in routes_to_remove:
            self.router.routes.remove(route)

        # Add custom route
        @self.router.post("/register", response_model=UserSchema)
        async def register(...):
            # Custom implementation
            pass
```

### Email System
Flexible transport system supporting multiple providers:
- Postmark (default, configured via `POSTMARK_API_TOKEN`)
- AWS SES (`mailer/transports/aws_ses_transport.py`)
- SMTP (`mailer/transports/smtp_transport.py`)

Templates stored in `mailer/templates/` as HTML files.

**Sending emails from API**:
```python
from api.dependencies.mailer import send_email_message

email_message = {
    "template": {
        "name": "registration",  # Corresponds to mailer/templates/registration.html
        "data": {
            "user": {"first_name": "John", "email": "john@example.com"},
            "subject": "Welcome!",
            "system_name": config.require_variable("NAME")
        }
    }
}
await send_email_message(email_message)
```

## Important Patterns & Conventions

### Creating New Entities
Follow this order to create a new entity (e.g., "Product"):

1. **Model** (`engine/models/product_model.py`):
```python
from engine.models.base_model import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class ProductModel(BaseModel):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    @classmethod
    def get_unique_identifier_field(cls):
        return cls.name  # Or whichever field is unique
```

2. **Schema** (`engine/schemas/product_schemas.py`):
```python
from engine.schemas.base_schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema
from typing import Optional

class ProductCreateSchema(BaseCreateSchema):
    name: str

class ProductUpdateSchema(BaseUpdateSchema):
    name: Optional[str] = None

class ProductSchema(BaseSchema):
    name: str
```

3. **Repository** (`engine/repositories/product_repository.py`):
```python
from engine.repositories.base_repository import BaseRepository
from engine.models.product_model import ProductModel

class ProductRepository(BaseRepository[ProductModel]):
    def __init__(self):
        super().__init__(ProductModel)
```

4. **Service** (`engine/services/product_service.py`):
```python
from engine.services.base_service import BaseService
from engine.models.product_model import ProductModel
from engine.repositories.product_repository import ProductRepository

class ProductService(BaseService[ProductModel]):
    def __init__(self):
        super().__init__(ProductRepository())
```

5. **API** (`api/v1/product_api.py`):
```python
from api.v1.base_api import BaseAPI
from engine.models.product_model import ProductModel
from engine.schemas.product_schemas import *
from engine.schemas.base_schemas import PaginatedResponse
from engine.services.product_service import ProductService

class ProductAPI(BaseAPI[ProductModel, ProductCreateSchema, ProductUpdateSchema, ProductSchema]):
    def __init__(self):
        self.service = ProductService()
        super().__init__(
            self.service,
            ProductSchema,
            ProductCreateSchema,
            ProductUpdateSchema,
            ProductModel,
            PaginatedResponse[ProductSchema]
        )

product_api = ProductAPI()
router = product_api.router
```

6. **Register** in `api/v1/router.py`:
```python
from api.v1.product_api import router as product_router
router.include_router(product_router, prefix="/products", tags=["Products"])
```

7. **Migration**: Generate and run migration:
```bash
alembic revision --autogenerate -m "Add products table"
alembic upgrade head
```

### Filtering and Pagination
Use `FilterParams` for pagination and `FilterCondition` for advanced queries:
```python
filters = [
    FilterCondition(field="status", operator="eq", value="active", type="str"),
    FilterCondition(field="created_at", operator="gte", value="2024-01-01", type="datetime")
]
params = FilterParams(limit=10, offset=0, search="query", sort_field="created_at", sort_direction="desc")
result = await service.get_all(db_conn, params=params, filters=filters)
```

Supported operators: `eq`, `neq`, `gt`, `lt`, `gte`, `lte`, `like`, `in`, `not_in`, `is_null`, `is_not_null`

### Audit Logging
All service operations automatically create audit logs when `token_data` is provided. Audit records include:
- Action performed (e.g., "user.create")
- User metadata (from TokenData)
- Entity metadata (entity-specific fields)
- Timestamp and status

### Versioning System
Models support versioning via reference fields:
- `reference_type`: Source system (e.g., "SILICA")
- `reference_name`: Field name (e.g., "TRANSNO")
- `reference_number`: Field value
- `version`: Integer version number
- `hash`: SHA-256 hash for change detection

Use `get_by_reference()` to fetch latest version or `get_all_hashes()` to check for updates.

### Relationship Loading
Relationships are loaded automatically via `selectinload` to prevent N+1 queries. The BaseAPI includes `_load_relationships_safely()` which handles relationship loading in the async context before response validation.

#### Rate Limiting
Redis-based rate limiting applied globally via middleware and per-endpoint via decorator:
- Configured via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` (in seconds)
- Uses sliding window algorithm with Redis sorted sets
- Rate limit headers added to all responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Window`
- Returns HTTP 429 when limit exceeded
- Rate limit keys are per-client-IP: `rate_limit:{client_ip}`

#### Error Handling
Standardized error responses via `api/dependencies/error_handler.py`:
```python
from api.dependencies.error_handler import ErrorHandling

# Use static methods for common errors
raise ErrorHandling.not_found("User not found")
raise ErrorHandling.already_exists("Email already registered")
raise ErrorHandling.permission_denied("Insufficient permissions")
raise ErrorHandling.invalid_credentials()
raise ErrorHandling.validation_error("Invalid input")
```

All errors are automatically logged. In production (`MODE != "development"`), error details are sanitized.

## Testing

Tests should be placed in the `tests/` directory. The project uses pytest with async support (`pytest-asyncio`).

Run tests with:
```bash
pytest
pytest -v  # Verbose output
pytest tests/test_specific.py  # Run specific test file
```

## Dependencies

Key dependencies:
- **FastAPI**: Web framework
- **SQLAlchemy 2.0**: Async ORM
- **Alembic**: Database migrations
- **asyncpg**: PostgreSQL async driver
- **Redis**: Session caching
- **Pydantic 2.0**: Data validation
- **PyJWT**: JWT token handling
- **aio-pika**: RabbitMQ async client

## Project Structure Notes

- Configuration files in `config/` are JSON-based and loaded by seeders
- Logs written to `logs/` directory (auto-created)
- Migration files in `migrations/versions/`
- All database operations are async (use `await`)
- All API endpoints require authentication except those in `auth_api.py`
- Rate limiting applied via `@rate_limit()` decorator on all endpoints
- The main application entry point is `api/__init__.py` (run with `python -m api`)
- OpenAPI docs available at `/api/docs` (Swagger UI) and `/api/redoc` (ReDoc)

## Common Gotchas

1. **Relationship loading**: Always use `await db_conn.refresh(model)` or selectinload for relationships after create/update
2. **Soft deletes**: By default, `delete()` soft-deletes (sets `is_deleted=True`). Use `hard_delete=True` to permanently remove
3. **Versioning**: If using versioning, implement `get_unique_identifier_field()` in your model
4. **Token expiration**: JWT tokens expire based on `JWT_EXPIRATION_MINUTES` environment variable
5. **Redis dependency**: The application requires Redis for both rate limiting and caching - ensure it's running
6. **Migration safety**: Always review auto-generated migrations before running them
7. **Error mode**: Set `MODE=production` to hide detailed error messages from API responses
8. **BaseAPI validation fallback**: If validation fails after create/update, BaseAPI falls back to safe dict representation to prevent errors
