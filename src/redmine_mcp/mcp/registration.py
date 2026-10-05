import asyncio

import httpx
from fastapi import Depends, FastAPI
from fastapi_mcp import AuthConfig, FastApiMCP
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from redmine_mcp.api import require_mcp_access
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
    validate_generated_tools(mcp.tools, operations)
    annotate_read_tools(mcp.tools)
    if settings is not None and settings.personal_writer:
        install_caller_discovery(mcp)
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
