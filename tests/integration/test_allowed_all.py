"""Expanded writer ceiling remains subordinate to reader, identity and resource gates."""

import json
from hashlib import sha256
from typing import Any

import httpx
import pytest

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS
from tests.helpers import mcp_session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode", ["reader", "personal", "restricted", "pinned", "wrong_pin", "permission"]
)
async def test_allowed_all_catalog_rest_and_capabilities_agree(
    application_factory: Any, synthetic: Any, mode: str
) -> None:
    config = {
        "redmine_write_enabled": mode != "reader",
        "redmine_writer_auth_mode": "pinned_key"
        if mode in {"pinned", "wrong_pin"}
        else "personal_key",
        "redmine_writer_operations": "allowed_all",
    }
    if mode in {"pinned", "wrong_pin"}:
        config.update(
            redmine_writer_user_ids="3",
            redmine_writer_key_sha256=sha256(b"offline-redmine-key").hexdigest(),
        )
    if mode == "restricted":
        config["redmine_writer_user_ids"] = "999"
    key = (
        "offline-rotated-key"
        if mode == "wrong_pin"
        else "offline-reader-key"
        if mode == "permission"
        else "offline-redmine-key"
    )
    async with application_factory(**config) as app:
        if mode == "wrong_pin":
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": key},
            ) as client:
                response = await client.post(
                    "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"}
                )
                assert response.status_code == 401
                response = await client.post(
                    "/api/v1/issues", json={"project_id": 7, "subject": "denied"}
                )
                assert response.status_code == 401
            assert synthetic.writes == 0
            return
        async with mcp_session(app, key) as session:
            names = {tool.name for tool in (await session.list_tools()).tools}
            if mode in {"personal", "pinned"}:
                assert names == set(READ_OPERATIONS) | set(WRITE_OPERATIONS)
            elif mode == "permission":
                assert names == set(READ_OPERATIONS) | {"upload_attachment"}
            else:
                assert names == set(READ_OPERATIONS)
            result = await session.call_tool(
                "list_my_project_capabilities", {"project_id": 7, "operation_id": "create_issue"}
            )
            assert not result.isError
            items = json.loads(result.content[0].text)["items"]
            if mode in {"personal", "pinned"}:
                assert items[0]["tools"][0]["state"] == "conditional"
            else:
                assert items == []  # Denied/disabled candidates are omitted by this filter.
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": key},
        ) as client:
            response = await client.post(
                "/api/v1/issues", json={"project_id": 7, "subject": "sentinel"}
            )
        assert response.status_code == (
            200 if mode in {"personal", "pinned"} else 401 if mode == "wrong_pin" else 403
        )
        assert synthetic.writes == (1 if mode in {"personal", "pinned"} else 0)


@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [("", set()), ("create_issue", {"create_issue"})])
async def test_explicit_empty_ceilings_remain_compatible(
    application_factory: Any, value: str, expected: set[str]
) -> None:
    async with application_factory(
        redmine_write_enabled=True,
        redmine_writer_auth_mode="personal_key",
        redmine_writer_operations=value,
    ) as app:
        async with mcp_session(app) as session:
            assert {t.name for t in (await session.list_tools()).tools} & set(
                WRITE_OPERATIONS
            ) == expected
