import asyncio

import httpx
from fastapi import Depends, FastAPI
from fastapi_mcp import AuthConfig, FastApiMCP
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from redmine_mcp.api import require_mcp_access
from redmine_mcp.bootstrap import read_budget_policy
from redmine_mcp.common.read_budget import ReadBudgetPolicy
from redmine_mcp.config import Settings
from redmine_mcp.constants import runtime as runtime_text
from redmine_mcp.mcp.annotations import annotate_read_tools
from redmine_mcp.mcp.catalog import (
    OPERATIONS,
    validate_generated_tools,
    validate_operation_catalog,
    writer_catalog,
)
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
    mcp = FastApiMCP(
        app,
        name="Redmine MCP",
        include_operations=list(operations),
        http_client=client,
        headers=["x-redmine-api-key"],
        auth_config=AuthConfig(dependencies=[Depends(require_mcp_access)]),
    )
    install_membership_transport(mcp)
    validate_generated_tools(mcp.tools, operations)
    repair_input_schemas(mcp.tools, app.openapi())
    for tool in mcp.tools:
        if tool.name in {"add_project_members", "update_project_members", "delete_project_members"}:
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
    if settings is not None and settings.personal_writer:
        install_caller_discovery(mcp)
    install_read_limits(mcp, read_budget_policy(settings) if settings else ReadBudgetPolicy())
    mcp.mount_http()
    return mcp


async def start_mcp(mcp: FastApiMCP) -> None:
    # FastAPI-MCP 0.4 sets its lazy-start flag before the SDK manager is ready.
    # Own startup here and publish that flag only after the SDK run context yields.
    # Keep all version-specific transport access in this adapter.
    transport = mcp._http_transport
    if transport is None or transport._manager_started:
        raise RuntimeError(runtime_text.MCP_START_FAILED)
    manager = StreamableHTTPSessionManager(
        app=transport.mcp_server,
        event_store=transport.event_store,
        json_response=transport.json_response,
        stateless=False,
        security_settings=transport.security_settings,
    )
    transport._session_manager = manager
    ready: asyncio.Future[None] = asyncio.get_running_loop().create_future()

    async def run_manager() -> None:
        try:
            async with manager.run():
                ready.set_result(None)
                await asyncio.Event().wait()
        except BaseException:
            if not ready.done():
                ready.set_exception(RuntimeError(runtime_text.MCP_START_FAILED))
            raise

    task = asyncio.create_task(run_manager())
    transport._manager_task = task
    try:
        await ready
    except BaseException:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        raise
    transport._manager_started = True


async def shutdown_mcp(mcp: FastApiMCP) -> None:
    # FastAPI-MCP 0.4 has no public server close method.
    if mcp._http_transport is not None:
        await mcp._http_transport.shutdown()
