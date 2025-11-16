"""
Schema definitions for the application.

This module organizes imports to avoid circular dependencies by:
1. Importing base schemas first
2. Importing simple/independent schemas next
3. Finally importing schemas that depend on other schemas
"""
from engine.schemas.address_schemas import AddressSchema, AddressUpdateSchema, AddressCreateSchema, AddressBaseSchema
# Base schemas must come first as they're used by all other schemas
from engine.schemas.base_schemas import (
    BaseSchema,
    BaseUpdateSchema,
    PaginationParams,
    PaginatedResponse,
    CountResponse,
    FilterOperator
)

from engine.schemas.address_schemas import (
    AddressSchema,
    AddressUpdateSchema,
    AddressCreateSchema,
    AddressBaseSchema,
)

from engine.schemas.comment_schemas import (
    CommentBaseSchema,
    CommentSchema,
    CommentCreateSchema,
    CommentUpdateSchema,
)

from engine.schemas.audit_schemas import (
    AuditBaseSchema,
    AuditCreateSchema,
    AuditUpdateSchema,
    AuditSchema
)


from engine.schemas.credential_schemas import (
    CredentialBaseSchema,
    CredentialCreateSchema,
    CredentialUpdateSchema,
    CredentialSchema
)

from engine.schemas.permission_schemas import (
    PermissionBaseSchema,
    PermissionCreateSchema,
    PermissionUpdateSchema,
    PermissionSchema
)

from engine.schemas.role_schemas import (
    RoleBaseSchema,
    RoleCreateSchema,
    RoleUpdateSchema,
    RoleSchema
)

from engine.schemas.token_schemas import (
    TokenBaseSchema,
    TokenCreateSchema,
    TokenUpdateSchema,
    TokenSchema
)

from engine.schemas.workspace_type_schemas import (
    WorkspaceTypeBaseSchema,
    WorkspaceTypeCreateSchema,
    WorkspaceTypeUpdateSchema,
    WorkspaceTypeSchema
)


# Intermediate complexity schemas with dependencies on simple types
from engine.schemas.role_permission_schemas import (
    RolePermissionBaseSchema,
    RolePermissionCreateSchema,
    RolePermissionUpdateSchema,
    RolePermissionSchema
)

from engine.schemas.user_credential_schemas import (
    UserCredentialBaseSchema,
    UserCredentialCreateSchema,
    UserCredentialUpdateSchema,
    UserCredentialSchema
)

from engine.schemas.user_schemas import (
    UserBaseSchema,
    UserCreateSchema,
    UserUpdateSchema,
    UserSchema,
    UserRegisterSchema
)

from engine.schemas.workspace_schemas import (
    WorkspaceBaseSchema,
    WorkspaceCreateSchema,
    WorkspaceUpdateSchema,
    WorkspaceSchema
)

from engine.schemas.workspace_address_schemas import (
    WorkspaceAddressBaseSchema,
    WorkspaceAddressCreateSchema,
    WorkspaceAddressUpdateSchema,
    WorkspaceAddressSchema
)

from engine.schemas.user_workspace_schemas import (
    UserWorkspaceBaseSchema,
    UserWorkspaceCreateSchema,
    UserWorkspaceUpdateSchema,
    UserWorkspaceSchema
)

from engine.schemas.auth_schemas import (
    SelfRegisterSchema,
    LoginSchema,
    PasswordChangeSchema,
    SessionSchema,
    SessionUserSchema,
    SessionTokenSchema,
    SessionWorkspaceSchema,
    SessionUserWorkspaceSchema,
    SessionRoleSchema,
    SessionPermissionSchema,
    SessionWorkspaceTypeSchema,
    OTPRequestSchema,
    PasswordResetSchema,
)

from engine.schemas.workflow_schemas import (
    WorkflowBaseSchema,
    WorkflowCreateSchema,
    WorkflowUpdateSchema,
    WorkflowSchema,
)

from engine.schemas.workflow_stage_schemas import (
    WorkflowStageBaseSchema,
    WorkflowStageCreateSchema,
    WorkflowStageUpdateSchema,
    WorkflowStageSchema,
)

from engine.schemas.approval_schema import (
    ApprovalBaseSchema,
    ApprovalCreateSchema,
    ApprovalUpdateSchema,
    ApprovalSchema,
)

from engine.schemas.attachment_schemas import (
    AttachmentBaseSchema,
    AttachmentCreateSchema,
    AttachmentUpdateSchema,
    AttachmentSchema,
)

from engine.schemas.file_schemas import (
    FileBaseSchema,
    FileCreateSchema,
    FileUpdateSchema,
    FileSchema,
    FileMetadata,
)


from engine.schemas.application_schemas import (
    ApplicationBaseSchema,
    ApplicationCreateSchema,
    ApplicationUpdateSchema,
    ApplicationSchema,
)


# Export all schemas
__all__ = [
    # Base schemas
    "BaseSchema",
    "BaseUpdateSchema",
    "PaginationParams",
    "PaginatedResponse",
    "CountResponse",
    "FilterOperator",

    # Auth schemas
    "SelfRegisterSchema",
    "LoginSchema",
    "PasswordChangeSchema",
    "SessionSchema",
    "SessionUserSchema",
    "SessionTokenSchema", 
    "SessionWorkspaceSchema",
    "SessionUserWorkspaceSchema",
    "SessionRoleSchema",
    "SessionPermissionSchema",
    "SessionWorkspaceTypeSchema",
    "OTPRequestSchema",
    "PasswordResetSchema",

    # User Management / Authentication
    # Address schemas
    "AddressBaseSchema",
    "AddressCreateSchema",
    "AddressUpdateSchema",
    "AddressSchema",
    
    # Audit schemas
    "AuditBaseSchema",
    "AuditCreateSchema",
    "AuditUpdateSchema",
    "AuditSchema",
    
    # Credential schemas
    "CredentialBaseSchema",
    "CredentialCreateSchema",
    "CredentialUpdateSchema",
    "CredentialSchema",
    
    # Permission schemas
    "PermissionBaseSchema",
    "PermissionCreateSchema",
    "PermissionUpdateSchema",
    "PermissionSchema",
    
    # Role Permission schemas
    "RolePermissionBaseSchema",
    "RolePermissionCreateSchema",
    "RolePermissionUpdateSchema",
    "RolePermissionSchema",
    
    # Role schemas
    "RoleBaseSchema",
    "RoleCreateSchema",
    "RoleUpdateSchema",
    "RoleSchema",
    
    # Token schemas
    "TokenBaseSchema",
    "TokenCreateSchema",
    "TokenUpdateSchema",
    "TokenSchema",
    
    # User Credential schemas
    "UserCredentialBaseSchema",
    "UserCredentialCreateSchema",
    "UserCredentialUpdateSchema",
    "UserCredentialSchema",
    
    # User schemas
    "UserBaseSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserSchema",
    "UserRegisterSchema",

    # User Workspace schemas
    "UserWorkspaceBaseSchema",
    "UserWorkspaceCreateSchema",
    "UserWorkspaceUpdateSchema",
    "UserWorkspaceSchema",

    # Workspace Address schemas
    "WorkspaceAddressBaseSchema",
    "WorkspaceAddressCreateSchema",
    "WorkspaceAddressUpdateSchema",
    "WorkspaceAddressSchema",
    
    # Workspace schemas
    "WorkspaceBaseSchema",
    "WorkspaceCreateSchema",
    "WorkspaceUpdateSchema",
    "WorkspaceSchema",
    
    # Workspace Type schemas
    "WorkspaceTypeBaseSchema",
    "WorkspaceTypeCreateSchema",
    "WorkspaceTypeUpdateSchema",
    "WorkspaceTypeSchema",

    # Geographic administrative divisions

    # Workflow
    # Workflow schemas
    "WorkflowBaseSchema",
    "WorkflowCreateSchema",
    "WorkflowUpdateSchema",
    "WorkflowSchema",
    "WorkflowStageBaseSchema",
    "WorkflowStageCreateSchema",
    "WorkflowStageUpdateSchema",
    "WorkflowStageSchema",
    "ApplicationBaseSchema",
    "ApplicationCreateSchema",
    "ApplicationUpdateSchema",
    "ApplicationSchema",
    "CommentBaseSchema",
    "CommentCreateSchema",
    "CommentUpdateSchema",
    "CommentSchema",

    # Approval schemas
    "ApprovalBaseSchema",
    "ApprovalCreateSchema",
    "ApprovalUpdateSchema",
    "ApprovalSchema",

    # Attachment schemas
    "AttachmentBaseSchema",
    "AttachmentCreateSchema",
    "AttachmentUpdateSchema",
    "AttachmentSchema",
    
    # File schemas
    "FileBaseSchema",
    "FileCreateSchema",
    "FileUpdateSchema",
    "FileSchema",
    "FileMetadata",

]
