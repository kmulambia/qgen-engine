from .__init__ import router
from api.v1.auth_api import router as auth_router
from api.v1.user_api import router as user_router
from api.v1.system_api import router as system_router
from api.v1.address_api import router as address_router
from api.v1.audit_api import router as audit_router
from api.v1.permission_api import router as permission_router
from api.v1.role_api import router as role_router
from api.v1.role_permission_api import router as role_permission_router
from api.v1.user_workspace_api import router as user_workspace_router
from api.v1.workspace_api import router as workspace_router
from api.v1.workspace_address_api import router as workspace_address_router
from api.v1.workspace_type_api import router as workspace_type_router
from api.v1.analytics_api import router as analytics_router
from api.v1.file_api import router as file_router
from api.v1.workflow_api import router as workflow_router
from api.v1.workflow_stage_api import router as workflow_stage_router
from api.v1.application_api import router as application_router
from api.v1.comment_api import router as comment_router
from api.v1.approval_api import router as approval_router
from api.v1.attachment_api import router as attachment_router
from api.v1.client_api import router as client_router

# System and Analytics
router.include_router(system_router, prefix="/system", tags=["System"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

# Authentication
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# User Management
router.include_router(user_router, prefix="/users", tags=["User"])
router.include_router(address_router, prefix="/addresses", tags=["Address"])
router.include_router(audit_router, prefix="/audits", tags=["Audit"])
router.include_router(permission_router, prefix="/permissions", tags=["Permission"])
router.include_router(role_router, prefix="/roles", tags=["Role"])
router.include_router(role_permission_router, prefix="/role-permissions", tags=["Role Permission"])
router.include_router(user_workspace_router, prefix="/user-workspaces", tags=["User Workspace"])
router.include_router(workspace_router, prefix="/workspaces", tags=["Workspace"])
router.include_router(workspace_address_router, prefix="/workspace-addresses", tags=["Workspace Addresses"])
router.include_router(workspace_type_router, prefix="/workspace-types", tags=["Workspace Types"])
router.include_router(file_router, prefix="/files", tags=["File"])
# Workflow
router.include_router(workflow_router, prefix="/workflows", tags=["Workflow"])
router.include_router(workflow_stage_router, prefix="/workflow-stages", tags=["Workflow Stages"])
router.include_router(application_router, prefix="/applications", tags=["Applications"])
router.include_router(comment_router, prefix="/comments", tags=["Comments"])
router.include_router(approval_router, prefix="/approvals", tags=["Approvals"])
router.include_router(attachment_router, prefix="/attachments", tags=["Attachments"])

# Client Management
router.include_router(client_router, prefix="/clients", tags=["Clients"])

