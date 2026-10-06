"""SDK session ownership must include both the caller and the current key."""

from typing import Any

import httpx
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["GET", "POST", "DELETE"])
@pytest.mark.parametrize("thief", ["offline-reader-key", "offline-rotated-key"])
async def test_other_identity_or_rotated_key_cannot_reuse_session(
    writer_app: Any, method: Any, thief: Any
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=writer_app),
        base_url="http://testserver",
        headers={
            "X-Redmine-API-Key": "offline-redmine-key",
            "Accept": "application/json, text/event-stream",
        },
    ) as client:
        initialized = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "offline", "version": "1"},
                },
            },
        )
        assert initialized.status_code == 200
        session_id = initialized.headers["mcp-session-id"]
        headers = {"Mcp-Session-Id": session_id, "Mcp-Protocol-Version": "2025-11-25"}
        await client.post(
            "/mcp", headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        response = await client.request(
            method,
            "/mcp",
            headers={**headers, "X-Redmine-API-Key": thief},
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"} if method == "POST" else None,
        )
        assert response.status_code == 404
        original = await client.post(
            "/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
        )
        assert original.status_code == 200
        await client.delete("/mcp", headers=headers)
