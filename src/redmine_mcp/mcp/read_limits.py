"""Keep MCP admission, safe error conversion and logical budget policy here."""

import json
from typing import Any

import httpx
from fastapi_mcp import FastApiMCP
from mcp import types

from redmine_mcp.auth import READ_OPERATIONS
from redmine_mcp.common import ApplicationError
from redmine_mcp.common.read_budget import ReadBudgetPolicy, current_budget, read_operation
from redmine_mcp.mcp.compatibility import MCPCompatibility


class MCPRestClient(httpx.AsyncClient):
    async def request(self, method: str, url: httpx.URL | str, **kwargs: Any) -> httpx.Response:
        response = await super().request(method, url, **kwargs)
        if response.is_error:
            # The internal ASGI response is already sanitized by our REST handlers.
            # Avoid the adapter's generic string containing the operation and response.
            data = response.json()
            error = data.get("error") if isinstance(data, dict) else None
            if not isinstance(error, dict) or not all(
                isinstance(error.get(field), str) for field in ("code", "message")
            ):
                # FastAPI validation errors can contain caller body values. Do not
                # include those values in the SDK's exception text or logs.
                error = {
                    "code": "invalid_parameters"
                    if response.status_code == 422
                    else "request_failed",
                    "message": "Invalid tool parameters"
                    if response.status_code == 422
                    else "Tool request failed",
                }
            raise RuntimeError(json.dumps({"error": error}, ensure_ascii=False))
        return response


def tool_error(code: str, message: str) -> types.ServerResult:
    return types.ServerResult(
        types.CallToolResult(
            isError=True,
            content=[
                types.TextContent(
                    type="text", text=json.dumps({"error": {"code": code, "message": message}})
                )
            ],
        )
    )


def install_read_limits(
    mcp: FastApiMCP,
    policy: ReadBudgetPolicy,
    *,
    compatibility: MCPCompatibility | None = None,
) -> None:
    # Prevent SDK lazy schema lookup from running a second discovery budget inside a call.
    if compatibility is None:
        compatibility = MCPCompatibility(mcp)
        compatibility.seed_tool_cache()
    original_call = compatibility.call_tool_handler()
    original_list = compatibility.list_tools_handler()
    operations = frozenset(tool.name for tool in compatibility.snapshot_tools())

    async def call_tool(request: types.CallToolRequest) -> types.ServerResult:
        name = request.params.name
        if name == "download_attachment":
            return tool_error(
                "attachment_download_disabled", "Use attachment metadata and its Redmine link"
            )
        if name not in operations:
            return tool_error("permission_denied", "Tool is not available in this deployment")
        if name not in READ_OPERATIONS:
            # A session task may have inherited transport authentication's context.
            # Writers must never inherit its expired budget or aggregate deadline.
            token = current_budget.set(None)
            try:
                return await original_call(request)
            finally:
                current_budget.reset(token)
        try:
            async with read_operation(policy, fresh=True):
                return await original_call(request)
        except ApplicationError as exc:
            return tool_error(exc.code, exc.message)

    async def list_tools(request: types.ListToolsRequest | None) -> types.ServerResult:
        from mcp.shared.exceptions import McpError

        try:
            async with read_operation(policy, fresh=True):
                return await original_list(request)
        except ApplicationError as exc:
            raise McpError(
                types.ErrorData(
                    code=types.INTERNAL_ERROR,
                    message=exc.message,
                    data={"status": exc.status, "code": exc.code},
                )
            ) from None

    compatibility.install_call_tool_handler(call_tool)
    compatibility.install_list_tools_handler(list_tools)
