"""Caller-specific discovery without mutating the SDK's shared tool schema cache."""

from fastapi import Request
from fastapi_mcp import FastApiMCP
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData, ListToolsRequest, ListToolsResult, ServerResult

from redmine_mcp.api.runtime import get_settings, get_upstream
from redmine_mcp.auth import WRITE_OPERATIONS, AuthContext
from redmine_mcp.bootstrap import build_capabilities
from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import auth as auth_text
from redmine_mcp.constants import runtime as runtime_text


def install_caller_discovery(mcp: FastApiMCP) -> None:
    server = mcp.server
    cache = getattr(server, "_tool_cache", None)
    if not isinstance(cache, dict):
        raise RuntimeError(runtime_text.MCP_START_FAILED)
    # SDK 1.30.0's list_tools decorator replaces this global cache on every list response.
    # Seed the immutable deployment superset once and register a raw response handler instead.
    tools = tuple(mcp.tools)
    cache.clear()
    cache.update({tool.name: tool.model_copy(deep=True) for tool in tools})
    write_operations = tuple(tool.name for tool in tools if tool.name in WRITE_OPERATIONS)

    async def list_tools(_request: ListToolsRequest | None) -> ServerResult:
        try:
            request = server.request_context.request
        except (LookupError, AttributeError):
            raise McpError(
                ErrorData(code=INTERNAL_ERROR, message=auth_text.PERMISSION_DENIED)
            ) from None
        if not isinstance(request, Request):
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=auth_text.PERMISSION_DENIED))
        context = getattr(request.state, "auth_context", None)
        if not isinstance(context, AuthContext):
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=auth_text.PERMISSION_DENIED))
        settings = get_settings(request)
        candidates: frozenset[str] = frozenset()
        admitted = not settings.writer_user_ids or (
            context.principal.redmine_user_id in settings.writer_user_ids
        )
        if settings.personal_writer and admitted and write_operations:
            capabilities = build_capabilities(
                get_upstream(request), context.api_key, settings, context.principal
            )
            try:
                candidates = await capabilities.candidates(write_operations)
            except ApplicationError as exc:
                raise McpError(
                    ErrorData(
                        code=INTERNAL_ERROR,
                        message=exc.message,
                        data={"status": exc.status, "code": exc.code},
                    )
                ) from None
        selected = [
            tool.model_copy(deep=True)
            for tool in tools
            if tool.name not in WRITE_OPERATIONS or tool.name in candidates
        ]
        for tool in selected:
            if tool.name in WRITE_OPERATIONS:
                tool.description = (tool.description or "") + (
                    " Permission depends on the target project and resource; "
                    "discovery does not guarantee invocation."
                )
        return ServerResult(ListToolsResult(tools=selected))

    server.request_handlers[ListToolsRequest] = list_tools
