"""G04: actual console safety, MCP correlation and unchanged transport semantics."""

import asyncio
import json
import logging
import re
from http import HTTPMethod
from typing import Any

import httpx
import pytest

from redmine_mcp.common import ApplicationError
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.transport import AdmittedTransport
from redmine_mcp.integrations.redmine.write import RedmineWriter
from redmine_mcp.observability import call_id, configure_logging, logical_call, request_id
from tests.helpers import mcp_session
from tests.logging_helpers import Console
from tests.logging_helpers import console as console
from tests.retry_helpers import RetryClock, RetryStream

pytestmark = pytest.mark.asyncio
SECRET = "sensitive-SENTINEL-83f17"


async def test_interleaved_mcp_discovery_tools_and_rejects_correlate_without_context_leaks(
    console: Console, application_factory: Any
) -> None:
    async with application_factory(log_level="DEBUG") as app:
        async with mcp_session(app) as session:
            console.clear()
            results = await asyncio.gather(
                session.list_tools(),
                session.call_tool("get_issue", {"issue_id": 42}),
                session.call_tool("get_project", {"project_id": 7}),
                session.call_tool(SECRET, {"private": SECRET}),
            )
            assert not results[1].isError and not results[2].isError
            assert results[3].isError
    starts = [r for r in console.records if r.getMessage().startswith("mcp_call_started")]
    ends = [r for r in console.records if r.getMessage().startswith("mcp_call_completed")]
    assert len(starts) == len(ends) == 4
    assert len({r.call_id for r in starts}) == 4
    assert all(re.fullmatch("[0-9a-f]{32}", r.call_id) for r in starts)
    for started in starts:
        group = [r for r in console.records if r.call_id == started.call_id]
        assert {r.request_id for r in group} == {started.request_id}
        assert sum(r.getMessage().startswith("mcp_call_completed") for r in group) == 1
        if "operation=get_" in started.getMessage():
            assert any(r.getMessage().startswith("upstream_attempt_started") for r in group)
            assert any(r.getMessage().startswith("request_completed operation=get_") for r in group)
        assert any(
            r.getMessage().startswith("request_completed operation=transport")
            and r.request_id == started.request_id
            for r in console.records
        )
    assert "operation=unknown" in console.output.getvalue()
    assert SECRET not in console.output.getvalue()
    assert request_id.get() == call_id.get() == "-"


@pytest.mark.parametrize("level", ["INFO", "DEBUG"])
async def test_rest_payload_cookie_url_and_native_exception_do_not_reach_console(
    console: Console, application_factory: Any, level: str
) -> None:
    async with application_factory(log_level=level) as app:

        @app.get("/private-error")
        async def private_error() -> None:
            raise RuntimeError(SECRET)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": "offline-redmine-key", "Cookie": SECRET},
        ) as client:
            response = await client.get(f"/api/v1/issues/42?private={SECRET}")
            assert response.status_code == 200
            rejected = await client.post(
                "/api/v1/uploads", json={"filename": SECRET, "content_base64": SECRET}
            )
            assert rejected.status_code in (403, 422)
            unexpected = await client.get(f"/private-error?private={SECRET}")
            assert unexpected.status_code == 500 and SECRET not in unexpected.text
    assert SECRET not in console.output.getvalue()
    assert "request_completed" in console.output.getvalue()
    assert (
        "request_started" in console.output.getvalue()
        if level == "DEBUG"
        else ("request_started" not in console.output.getvalue())
    )


@pytest.mark.parametrize("level", ["INFO", "DEBUG"])
@pytest.mark.parametrize("fault", ["retry", "malformed", "cancel"])
async def test_debug_preserves_read_retry_stream_cleanup_and_permit_release(
    console: Console, level: str, fault: str
) -> None:
    configure_logging(level)
    streams: list[RetryStream] = []
    requests: list[httpx.Request] = []
    clock = RetryClock()
    semaphore = asyncio.Semaphore(1)

    async def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if fault == "cancel":
            raise asyncio.CancelledError(SECRET)
        first = len(requests) == 1
        stream = RetryStream(
            (b"invalid " + SECRET.encode(),)
            if fault == "malformed"
            else (json.dumps({"value": SECRET}).encode(),)
        )
        streams.append(stream)
        return httpx.Response(503 if fault == "retry" and first else 200, stream=stream)

    async with httpx.AsyncClient(
        base_url=f"http://{SECRET.lower()}.invalid/",
        transport=AdmittedTransport(httpx.MockTransport(respond), semaphore, 1),
        headers={"Authorization": SECRET},
        cookies={"session": SECRET},
    ) as http:
        client = RedmineClient(http, SECRET, retry_runtime=clock.runtime())
        try:
            with logical_call("get_issue", None):
                result = await client.get("issues/42.json", {"private": SECRET})
            assert fault == "retry" and result == {"value": SECRET}
        except ApplicationError as error:
            assert fault == "malformed" and error.code == "upstream_response"
        except asyncio.CancelledError:
            assert fault == "cancel"
    assert len(requests) == (2 if fault == "retry" else 1)
    assert clock.waits == ([0.5] if fault == "retry" else [])
    assert all(s.closed == 1 for s in streams)
    assert semaphore._value == 1
    assert all("cookie" not in r.headers and "authorization" not in r.headers for r in requests)
    assert SECRET.lower() not in console.output.getvalue().lower()
    assert request_id.get() == call_id.get() == "-"


@pytest.mark.parametrize("level", ["INFO", "DEBUG"])
@pytest.mark.parametrize("status", [204, 422, 503])
async def test_debug_preserves_write_receipts_without_retry_or_credential_logging(
    console: Console, level: str, status: int
) -> None:
    configure_logging(level)
    requests: list[httpx.Request] = []
    stream = RetryStream((SECRET.encode(),))
    semaphore = asyncio.Semaphore(1)

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        logging.getLogger("httpcore.connection").error("native body %s", SECRET)
        return httpx.Response(status, stream=stream)

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=AdmittedTransport(httpx.MockTransport(respond), semaphore, 1),
    ) as http:
        writer = RedmineWriter(http, SECRET, ReadPolicy())
        try:
            receipt = await writer.write_json(
                HTTPMethod.PUT, "issues/42.json", {"issue": {"subject": SECRET}}
            )
            assert receipt.outcome == ("accepted" if status == 204 else "uncertain")
        except Exception as error:
            from redmine_mcp.integrations.redmine.write import RedmineWriteRejected

            assert status == 422 and isinstance(error, RedmineWriteRejected)
    assert len(requests) == stream.closed == semaphore._value == 1
    assert SECRET not in console.output.getvalue()
    assert "vendor_diagnostic details_omitted=true" in console.output.getvalue()


@pytest.mark.parametrize("level", ["INFO", "DEBUG"])
async def test_upload_filename_token_and_binary_bytes_are_not_logged(
    console: Console, level: str
) -> None:
    configure_logging(level)
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json={"upload": {"token": SECRET, "id": 9}})

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        receipt = await RedmineWriter(http, SECRET, ReadPolicy()).write_binary(
            "uploads.json", SECRET.encode(), filename=SECRET + ".txt"
        )
    assert receipt.outcome == "accepted" and receipt.payload["upload"]["token"] == SECRET
    assert len(requests) == 1 and requests[0].url.params["filename"] == SECRET + ".txt"
    assert SECRET not in console.output.getvalue()
