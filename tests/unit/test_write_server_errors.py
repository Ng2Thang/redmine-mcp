"""Received mutation errors never consume bodies or retry, including binary uploads."""

from collections.abc import AsyncIterator

import httpx
import pytest

from redmine_mcp.common import ApplicationError
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.write import RedmineWriter


class UnreadableErrorStream(httpx.AsyncByteStream):
    def __init__(self) -> None:
        self.closed = False
        self.reads = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        self.reads += 1
        raise AssertionError("Server error body must not be consumed")
        yield b""  # pragma: no cover

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [500, 503, 504, 599])
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "binary"])
async def test_error_stream_closed_without_read_or_retry(status: int, method: str) -> None:
    stream = UnreadableErrorStream()
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status, stream=stream)

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid", transport=httpx.MockTransport(respond)
    ) as client:
        writer = RedmineWriter(client, "offline-redmine-key", ReadPolicy())
        if method == "binary":
            receipt = await writer.write_binary("uploads.json", b"x", filename="x.txt")
        else:
            receipt = await writer.write_json(method, "issues/42.json")  # type: ignore[arg-type]
        assert receipt.outcome == "uncertain" and receipt.status == status
        assert receipt.payload is None
    assert len(requests) == 1 and stream.closed and stream.reads == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure,expected_status,code",
    [
        (httpx.PoolTimeout("private-error"), 503, "upstream_busy"),
        (httpx.ConnectError("private-error"), 502, "upstream_unavailable"),
    ],
)
async def test_admission_failure_does_not_invent_dispatched_uncertainty(
    failure: httpx.RequestError, expected_status: int, code: str
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        request.extensions["redmine_dispatched"] = False
        raise failure

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid", transport=httpx.MockTransport(respond)
    ) as client:
        with pytest.raises(ApplicationError) as error:
            await RedmineWriter(client, "offline-redmine-key", ReadPolicy()).write_json(
                "POST", "issues.json", {"issue": {"project_id": 7, "subject": "x"}}
            )
    assert error.value.status == expected_status and error.value.code == code
    assert "private-error" not in str(error.value)
