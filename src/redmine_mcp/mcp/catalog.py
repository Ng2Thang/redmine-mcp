"""Explicit MCP exposure policy for the REST-backed tool catalog."""

from collections import Counter
from http import HTTPMethod

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from mcp.types import Tool

from redmine_mcp.api import require_read_access, require_write_access, route_contracts
from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS
from redmine_mcp.constants import mcp as mcp_text

OPERATIONS = (
    "get_current_user",
    "list_my_project_capabilities",
    "list_projects",
    "get_project",
    "list_project_versions",
    "list_project_issue_categories",
    "list_project_files",
    "list_project_time_entry_activities",
    "list_project_members",
    "list_issues",
    "get_issue",
    "get_attachment",
    "list_issue_time_entries",
    "list_time_entries",
    "list_issue_statuses",
    "list_issue_priorities",
    "list_document_categories",
    "list_trackers",
)


def has_read_dependency(dependency: Dependant) -> bool:
    return dependency.call is require_read_access or any(
        has_read_dependency(child) for child in dependency.dependencies
    )


def has_write_dependency(dependency: Dependant) -> bool:
    return dependency.call is require_write_access or any(
        has_write_dependency(child) for child in dependency.dependencies
    )


def writer_catalog(configured: frozenset[str]) -> tuple[str, ...]:
    unknown = configured.difference(WRITE_OPERATIONS)
    if unknown:
        raise ValueError(mcp_text.UNKNOWN_WRITE_OPERATIONS.format(operations=sorted(unknown)))
    return (*OPERATIONS, *(name for name in WRITE_OPERATIONS if name in configured))


def validate_generated_tools(tools: list[Tool], operations: tuple[str, ...] = OPERATIONS) -> None:
    if Counter(tool.name for tool in tools) != Counter(operations):
        raise ValueError(mcp_text.CATALOG_MISMATCH)


def validate_operation_catalog(app: FastAPI, operations: tuple[str, ...] = OPERATIONS) -> None:
    """Require each exposed operation to have one authorized versioned route."""
    duplicates = [name for name, count in Counter(operations).items() if count > 1]
    if duplicates:
        raise ValueError(mcp_text.DUPLICATE_OPERATION_IDS.format(operations=", ".join(duplicates)))
    unauthorized = set(OPERATIONS).difference(READ_OPERATIONS)
    if unauthorized:
        raise ValueError(mcp_text.MISSING_READ_PERMISSIONS.format(operations=sorted(unauthorized)))

    routes = route_contracts(app)
    for name in operations:
        matches = [route for route in routes if route.operation_id == name]
        if len(matches) != 1:
            raise ValueError(mcp_text.UNIQUE_ROUTE_REQUIRED.format(operation=name))
        route = matches[0]
        if name in OPERATIONS:
            if not route.path.startswith("/api/v1/") or route.methods != {HTTPMethod.GET}:
                raise ValueError(mcp_text.GET_ROUTE_REQUIRED.format(operation=name))
            if not has_read_dependency(route.dependant):
                raise ValueError(mcp_text.READ_AUTHORIZATION_REQUIRED.format(operation=name))
        elif name in WRITE_OPERATIONS:
            if not route.path.startswith("/api/v1/") or route.methods not in (
                {HTTPMethod.POST},
                {HTTPMethod.PUT},
                {HTTPMethod.PATCH},
                {HTTPMethod.DELETE},
            ):
                raise ValueError(mcp_text.WRITE_ROUTE_REQUIRED.format(operation=name))
            if not has_write_dependency(route.dependant):
                raise ValueError(mcp_text.WRITE_AUTHORIZATION_REQUIRED.format(operation=name))
        else:
            raise ValueError(mcp_text.UNKNOWN_WRITE_OPERATIONS.format(operations=[name]))
        if not route.publishes_response:
            raise ValueError(mcp_text.RESPONSE_SCHEMA_REQUIRED.format(operation=name))
