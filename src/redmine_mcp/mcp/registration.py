import httpx
from fastapi import Depends, FastAPI
from fastapi_mcp import AuthConfig, FastApiMCP

from redmine_mcp.api import require_mcp_access
from redmine_mcp.bootstrap import read_budget_policy
from redmine_mcp.common.read_budget import ReadBudgetPolicy
from redmine_mcp.config import Settings
from redmine_mcp.mcp.annotations import annotate_read_tools
from redmine_mcp.mcp.catalog import (
    OPERATIONS,
    validate_generated_tools,
    validate_operation_catalog,
    writer_catalog,
)
from redmine_mcp.mcp.compatibility import MCPCompatibility
from redmine_mcp.mcp.discovery import install_caller_discovery
from redmine_mcp.mcp.membership_transport import install_membership_transport
from redmine_mcp.mcp.read_limits import install_read_limits
from redmine_mcp.mcp.schema import repair_input_schemas


def register_mcp(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings | None = None
) -> FastApiMCP:
    operations = (
        writer_catalog(settings.writer_operations)
        if settings is not None and settings.redmine_write_enabled
        else OPERATIONS
    )
    validate_operation_catalog(app, operations)
    MCPCompatibility.check_versions()
    mcp = FastApiMCP(
        app,
        name="Redmine MCP",
        include_operations=list(operations),
        http_client=client,
        headers=["x-redmine-api-key"],
        auth_config=AuthConfig(dependencies=[Depends(require_mcp_access)]),
    )
    compatibility = MCPCompatibility(mcp)
    install_membership_transport(mcp, compatibility=compatibility)
    validate_generated_tools(mcp.tools, operations)
    repair_input_schemas(mcp.tools, app.openapi())
    for tool in mcp.tools:
        if tool.name in {
            "create_time_entry",
            "add_project_members",
            "update_project_members",
            "delete_project_members",
            "delete_time_entry",
        }:
            tool.inputSchema["additionalProperties"] = False
        if tool.name in {
            "list_projects",
            "list_issues",
            "list_issue_time_entries",
            "list_my_project_capabilities",
            "list_project_members",
        }:
            tool.description = (tool.description or "") + (
                " The first page may be a discovery preview. Check pagination_policy: "
                "when requires_narrowing is true, narrow scope before requesting another "
                "page. The server limits total matching pages and read work; do not "
                "continue on scope_required or scan_budget_exceeded."
            )
    annotate_read_tools(mcp.tools)
    compatibility.seed_tool_cache()
    if settings is not None and settings.redmine_write_enabled:
        install_caller_discovery(mcp, compatibility=compatibility)
    install_read_limits(
        mcp,
        read_budget_policy(settings) if settings else ReadBudgetPolicy(),
        compatibility=compatibility,
    )
    compatibility.mount_transport()
    return mcp


async def start_mcp(mcp: FastApiMCP) -> None:
    await MCPCompatibility(mcp).start()


async def shutdown_mcp(mcp: FastApiMCP) -> None:
    await MCPCompatibility(mcp).shutdown()
