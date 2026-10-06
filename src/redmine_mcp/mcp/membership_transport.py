"""Keep FastAPI-MCP 0.4's DELETE-body compatibility at the adapter boundary."""

from collections.abc import Awaitable, Callable
from typing import Any, cast

import httpx
from fastapi_mcp import FastApiMCP


def install_membership_transport(mcp: FastApiMCP) -> None:
    original = cast(
        Callable[
            [httpx.AsyncClient, str, str, dict[str, Any], dict[str, str], Any], Awaitable[Any]
        ],
        mcp._request,
    )

    async def request(
        client: httpx.AsyncClient,
        method: str,
        path: str,
        query: dict[str, Any],
        headers: dict[str, str],
        body: Any | None,
    ) -> Any:
        if method.lower() == "delete" and path == "/api/v1/projects/memberships/batch":
            return await client.request("DELETE", path, params=query, headers=headers, json=body)
        return await original(client, method, path, query, headers, body)

    mcp._request = request
