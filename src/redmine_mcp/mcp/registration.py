import httpx
from fastapi import Depends, FastAPI
from fastapi_mcp import AuthConfig, FastApiMCP

from redmine_mcp.api import require_mcp_access
from redmine_mcp.mcp.annotations import annotate_read_tools
from redmine_mcp.mcp.catalog import (
    OPERATIONS,
    validate_generated_tools,
    validate_operation_catalog,
)


def register_mcp(app: FastAPI, client: httpx.AsyncClient) -> FastApiMCP:
    validate_operation_catalog(app)
    mcp = FastApiMCP(
        app,
        name="Redmine MCP",
        include_operations=list(OPERATIONS),
        http_client=client,
        headers=["x-redmine-api-key"],
        auth_config=AuthConfig(dependencies=[Depends(require_mcp_access)]),
    )
    validate_generated_tools(mcp.tools)
    annotate_read_tools(mcp.tools)
    mcp.mount_http()
    return mcp


async def shutdown_mcp(mcp: FastApiMCP) -> None:
    # FastAPI-MCP 0.4 starts this task lazily but has no public server close method.
    # Keep this version-specific lifecycle access isolated in the MCP adapter.
    if mcp._http_transport is not None:
        await mcp._http_transport.shutdown()
