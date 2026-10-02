from fastapi import status as http_status

from redmine_mcp.auth.models import Principal
from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import auth as auth_text
from redmine_mcp.constants import codes as codes_text

READ_OPERATIONS = (
    "get_current_user",
    "list_projects",
    "get_project",
    "list_project_versions",
    "list_project_issue_categories",
    "list_issues",
    "get_issue",
    "list_issue_time_entries",
    "list_issue_statuses",
    "list_issue_priorities",
    "list_document_categories",
    "list_trackers",
)


class AuthorizationPolicy:
    """Explicit application permissions; Redmine owns resource visibility."""

    def __init__(self, read_operations: tuple[str, ...]) -> None:
        self.permissions = frozenset(f"read:{operation}" for operation in read_operations)

    def authorize(self, principal: Principal, permission: str) -> None:
        if (
            type(principal.redmine_user_id) is not int
            or principal.redmine_user_id < 1
            or (permission != "mcp:connect" and permission not in self.permissions)
        ):
            raise ApplicationError(
                codes_text.PERMISSION_DENIED,
                auth_text.PERMISSION_DENIED,
                http_status.HTTP_403_FORBIDDEN,
            )
