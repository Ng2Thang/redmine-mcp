"""Explicit MCP exposure policy for the REST-backed tool catalog."""

from collections import Counter

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from mcp.types import Tool

from redmine_mcp.api import require_read_access, route_contracts
from redmine_mcp.auth import READ_OPERATIONS

OPERATIONS = (
    "list_projects",
    "get_project",
    "list_project_versions",
    "list_project_issue_categories",
    "list_issues",
    "get_issue",
    "list_issue_time_entries",
    "list_issue_statuses",
    "list_trackers",
    "list_issue_priorities",
)


def has_read_dependency(dependency: Dependant) -> bool:
    return dependency.call is require_read_access or any(
        has_read_dependency(child) for child in dependency.dependencies
    )


def validate_generated_tools(tools: list[Tool]) -> None:
    if Counter(tool.name for tool in tools) != Counter(OPERATIONS):
        raise ValueError("Generated MCP tools do not match the explicit catalog")


def validate_operation_catalog(app: FastAPI) -> None:
    """Require each exposed tool to have one GET route in the versioned API."""
    duplicates = [name for name, count in Counter(OPERATIONS).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate MCP operation IDs in catalog: {', '.join(duplicates)}")
    unauthorized = set(OPERATIONS).difference(READ_OPERATIONS)
    if unauthorized:
        raise ValueError(f"MCP operations lack explicit read permissions: {sorted(unauthorized)}")

    routes = route_contracts(app)
    for name in OPERATIONS:
        matches = [route for route in routes if route.operation_id == name]
        if len(matches) != 1:
            raise ValueError(f"MCP operation {name!r} must match exactly one REST route")
        route = matches[0]
        if not route.path.startswith("/api/v1/") or route.methods != {"GET"}:
            raise ValueError(f"MCP operation {name!r} must use a GET route under /api/v1/")
        if not route.publishes_response:
            raise ValueError(f"MCP operation {name!r} must publish a response schema")
        if not has_read_dependency(route.dependant):
            raise ValueError(f"MCP operation {name!r} must enforce read authorization")
