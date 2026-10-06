"""Current bounded-read regressions without large live datasets."""

import asyncio
from typing import Any

import httpx
import pytest

from redmine_mcp.common import ApplicationError
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.transport import AdmittedTransport, create_upstream_client
from tests.helpers import ISSUE, mcp_session


@pytest.mark.asyncio
async def test_million_record_preview_and_rejected_continuation(
    rest_client: Any, upstream: Any
) -> None:
    upstream["body"] = {"issues": [ISSUE], "total_count": 1000000}
    result = await rest_client.get("/api/v1/issues")
    assert result.status_code == 200
    assert result.json()["pagination_policy"] == {
        "total_pages": 40000,
        "max_query_pages": 10,
        "requires_narrowing": True,
    }
    before = len(upstream["requests"])
    result = await rest_client.get("/api/v1/issues", params={"offset": 25, "project_id": 7})
    assert result.status_code == 422 and result.json()["error"]["code"] == "scope_required"
    resources = [r for r in upstream["requests"][before:] if r.url.path == "/issues.json"]
    assert len(resources) == 1
    assert dict(resources[0].url.params) == {
        "limit": "1",
        "offset": "0",
        "project_id": "7",
        "status_id": "open",
        "sort": "id:asc",
    }


@pytest.mark.asyncio
async def test_retired_download_rest_and_cached_mcp_fetch_nothing(
    app: Any, rest_client: Any, upstream: Any
) -> None:
    result = await rest_client.get("/api/v1/attachments/9/content")
    assert result.status_code == 403
    assert upstream["requests"] == []
    async with mcp_session(app) as session:
        assert "download_attachment" not in {t.name for t in (await session.list_tools()).tools}
        before = len(upstream["requests"])
        result = await session.call_tool("download_attachment", {"attachment_id": 9})
        assert result.isError
        assert all(r.url.path == "/users/current.json" for r in upstream["requests"][before:])


@pytest.mark.parametrize(
    "url",
    [
        "https://other.invalid/attachments/download/9/x",
        "http://redmine.invalid/attachments/download/8/x",
        "http://redmine.invalid/attachments/download/9/%2e%2e/x",
        "http://secret@redmine.invalid/attachments/download/9/x",
        "http://redmine.invalid/attachments/download/9/x?key=secret",
    ],
)
@pytest.mark.asyncio
async def test_attachment_link_rejects_unsafe_metadata(url: Any) -> None:
    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=httpx.MockTransport(lambda r: httpx.Response(200)),
    ) as http:
        with pytest.raises(ApplicationError) as error:
            RedmineClient(http, "fake").attachment_link(url, 9)
        assert error.value.status == 502


@pytest.mark.asyncio
async def test_attachment_subpath_mapping_never_fetches_bytes() -> None:
    requests = []

    def respond(request: Any) -> Any:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "attachment": {
                    "id": 9,
                    "filesize": 1,
                    "content_url": "http://redmine.invalid/internal/attachments/download/9/x",
                }
            },
        )

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/internal/", transport=httpx.MockTransport(respond)
    ) as http:
        client = RedmineClient(
            http, "fake", ReadPolicy(public_url="https://public.invalid/redmine/")
        )
        data = await client.get("attachments/9.json", {})
    assert (
        data["attachment"]["content_url"]
        == "https://public.invalid/redmine/attachments/download/9/x"
    )
    assert len(requests) == 1 and requests[0].url.path == "/internal/attachments/9.json"


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [2, 50])
async def test_admission_contention_held_until_close(limit: Any) -> None:
    semaphore = asyncio.Semaphore(limit)
    dispatched = 0

    def respond(request: Any) -> Any:
        nonlocal dispatched
        dispatched += 1
        return httpx.Response(200, stream=httpx.ByteStream(b"x"))

    async with httpx.AsyncClient(
        transport=AdmittedTransport(httpx.MockTransport(respond), semaphore, 0.02)
    ) as http:
        responses = await asyncio.gather(
            *(
                http.send(http.build_request("GET", "http://redmine.invalid"), stream=True)
                for _ in range(limit)
            )
        )
        with pytest.raises(ApplicationError) as error:
            await http.send(http.build_request("GET", "http://redmine.invalid"), stream=True)
        assert error.value.code == "upstream_busy"
        assert dispatched == limit
        await asyncio.gather(*(r.aclose() for r in responses))
        response = await http.send(http.build_request("GET", "http://redmine.invalid"), stream=True)
        await response.aclose()
        assert dispatched == limit + 1
    assert semaphore._value == limit


@pytest.mark.asyncio
async def test_direct_and_proxy_mounts_share_admission(
    fake_settings: Any, monkeypatch: Any
) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:8080")
    monkeypatch.setenv("ALL_PROXY", "http://fallback.invalid:8080")
    monkeypatch.setenv("NO_PROXY", "bypass.invalid")
    transports = []

    def fake_transport(**kwargs: Any) -> Any:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, stream=httpx.ByteStream(b"x"))
        )
        transports.append((kwargs.get("proxy"), transport))
        return transport

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", fake_transport)
    async with create_upstream_client(fake_settings) as http:
        direct = http._transport_for_url(httpx.URL("http://bypass.invalid"))
        proxy = http._transport_for_url(httpx.URL("http://target.invalid"))
        secure = http._transport_for_url(httpx.URL("https://target.invalid"))
        assert direct is not proxy
        assert direct.semaphore is proxy.semaphore is secure.semaphore
        await http.get("http://bypass.invalid")
        await http.get("http://target.invalid")
        assert direct.semaphore._value == fake_settings.redmine_max_concurrent_requests
    assert {p for p, _ in transports} >= {
        None,
        "http://proxy.invalid:8080",
        "http://fallback.invalid:8080",
    }


@pytest.mark.asyncio
async def test_expired_synchronous_response_returns_504_before_headers(
    application_factory: Any, synthetic: Any
) -> None:
    from redmine_mcp.api.read_limits import ReadLimitsMiddleware
    from redmine_mcp.common.read_budget import ReadBudgetPolicy, current_budget

    async def endpoint(scope: Any, receive: Any, send: Any) -> Any:
        current_budget.get().started -= 100
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    middleware = ReadLimitsMiddleware(endpoint, ReadBudgetPolicy())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=middleware), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/conversion")
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "read_operation_timeout"


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_auth_and_resource_share_request_budget(
    application_factory: Any, boundary: Any
) -> None:
    async with application_factory(redmine_read_operation_max_requests=1) as app:
        if boundary == "rest":
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": "offline-redmine-key"},
            ) as client:
                response = await client.get("/api/v1/projects")
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "scan_budget_exceeded"
        else:
            async with mcp_session(app) as session:
                result = await session.call_tool("list_projects", {})
                assert result.isError and "scan_budget_exceeded" in str(result.content)
