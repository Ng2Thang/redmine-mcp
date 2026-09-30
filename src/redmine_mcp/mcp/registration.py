import httpx
from fastapi import Depends, FastAPI
from fastapi_mcp import AuthConfig, FastApiMCP

from redmine_mcp.api.security import require_token

OPERATIONS = [
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
]


def register_mcp(app: FastAPI, client: httpx.AsyncClient) -> FastApiMCP:
    mcp = FastApiMCP(
        app,
        name="Redmine MCP",
        include_operations=OPERATIONS,
        http_client=client,
        headers=["authorization"],
        auth_config=AuthConfig(dependencies=[Depends(require_token)]),
    )
    mcp.mount_http()
    return mcp


async def shutdown_mcp(mcp: FastApiMCP) -> None:
    # FastAPI-MCP 0.4 starts this task lazily but has no public server close method.
    # Keep this version-specific lifecycle access isolated in the MCP adapter.
    if mcp._http_transport is not None:
        await mcp._http_transport.shutdown()
