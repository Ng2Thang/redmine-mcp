"""Public HTTP adapters and dependency entry points."""

from redmine_mcp.api.dependencies import (
    get_container,
    get_issues,
    get_projects,
    get_reference_data,
    get_time_entries,
    get_users,
)
from redmine_mcp.api.error_handlers import application_error, unexpected_error
from redmine_mcp.api.health import router as health_router
from redmine_mcp.api.middleware import RequestContextMiddleware
from redmine_mcp.api.routing import RouteContract, route_contracts
from redmine_mcp.api.runtime import get_settings, get_upstream
from redmine_mcp.api.security import (
    get_auth_context,
    require_mcp_access,
    require_read_access,
    require_write_access,
)

__all__ = [
    "RequestContextMiddleware",
    "RouteContract",
    "application_error",
    "get_auth_context",
    "get_container",
    "get_issues",
    "get_projects",
    "get_reference_data",
    "get_settings",
    "get_time_entries",
    "get_upstream",
    "get_users",
    "health_router",
    "require_mcp_access",
    "require_read_access",
    "require_write_access",
    "route_contracts",
    "unexpected_error",
]
