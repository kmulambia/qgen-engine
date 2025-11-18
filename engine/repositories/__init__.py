# User Management / Authentication
from engine.repositories.address_repository import AddressRepository
from engine.repositories.audit_repository import AuditRepository
from engine.repositories.credential_repository import CredentialRepository
from engine.repositories.permission_repository import PermissionRepository
from engine.repositories.role_repository import RoleRepository
from engine.repositories.role_permission_repository import RolePermissionRepository
from engine.repositories.token_repository import TokenRepository
from engine.repositories.user_credential_repository import UserCredentialRepository
from engine.repositories.user_repository import UserRepository
from engine.repositories.user_workspace_repository import UserWorkspaceRepository
from engine.repositories.workspace_repository import WorkspaceRepository
from engine.repositories.workspace_address_repository import WorkspaceAddressRepository
from engine.repositories.workspace_type_repository import WorkspaceTypeRepository
from engine.repositories.otp_repository import OTPRepository

# Workflow
from engine.repositories.workflow_repository import WorkflowRepository
from engine.repositories.workflow_stage_repository import WorkflowStageRepository
from engine.repositories.application_repository import ApplicationRepository
from engine.repositories.approval_repository import ApprovalRepository
from engine.repositories.comment_repository import CommentRepository
from engine.repositories.file_repository import FileRepository
from engine.repositories.attachment_repository import AttachmentRepository

# Client Management
from engine.repositories.client_repository import ClientRepository

# Layouts
from engine.repositories.layout_repository import LayoutRepository

# Quotations
from engine.repositories.quotation_repository import QuotationRepository

__all__ = [
    # User Management / Authentication
    "AddressRepository",
    "AuditRepository",
    "CredentialRepository",
    "PermissionRepository",
    "RoleRepository",
    "RolePermissionRepository",
    "TokenRepository",
    "UserCredentialRepository",
    "UserRepository",
    "UserWorkspaceRepository",
    "WorkspaceRepository",
    "WorkspaceAddressRepository",
    "WorkspaceTypeRepository",
    "OTPRepository",
    
    # Workflow
    "WorkflowRepository",
    "WorkflowStageRepository",
    "ApplicationRepository",
    "ApprovalRepository",
    "CommentRepository",
    "FileRepository",
    "AttachmentRepository",

    # Client Management
    "ClientRepository",
    
    # Layouts
    "LayoutRepository",
    
    # Quotations
    "QuotationRepository",
]
