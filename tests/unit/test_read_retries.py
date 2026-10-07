"""PREP-027 deterministic delay/configuration and shared GET recovery contracts."""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from email.utils import format_datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from redmine_mcp.bootstrap import build_authentication, read_policy
from redmine_mcp.common import ApplicationError
from redmine_mcp.common.read_budget import ReadBudget, ReadBudgetPolicy, current_budget
from redmine_mcp.config import Settings
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.identity import RedmineIdentity
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.retry import (
    RETRY_ERRORS,
    RETRY_STATUSES,
    RetryRuntime,
    retry_after_seconds,
)
from redmine_mcp.integrations.redmine.transport import AdmittedTransport
from redmine_mcp.integrations.redmine.write import RedmineWriter
from tests.retry_helpers import RetryClock, RetryStream


@pytest.mark.parametrize("failure", [*sorted(RETRY_STATUSES), *RETRY_ERRORS])
@pytest.mark.asyncio
async def test_eligible_failure_recovers_with_fresh_authenticated_request(failure: Any) -> None:
    requests: list[httpx.Request] = []
    clock = RetryClock()

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            if isinstance(failure, int):
                return httpx.Response(failure, stream=RetryStream())
            raise failure("private-exception-value")
        return httpx.Response(200, json={"value": 7})

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        http.cookies.set("shared", "private-cookie")
        http.headers["Authorization"] = "private-auth"
        data = await RedmineClient(http, "private-key", retry_runtime=clock.runtime()).get(
            "issues/7.json", {"include": "journals,attachments"}
        )
    assert data == {"value": 7}
    assert len(requests) == 2 and requests[0] is not requests[1]
    assert clock.waits == [0.5]
    for request in requests:
        assert request.headers["X-Redmine-API-Key"] == "private-key"
        assert "cookie" not in request.headers and "authorization" not in request.headers
        assert dict(request.url.params) == {"include": "journals,attachments"}


@pytest.mark.parametrize(
    ("failure", "code", "status"),
    [
        (429, "upstream_rate_limited", 502),
        (502, "upstream_error", 502),
        (503, "upstream_unavailable", 502),
        (504, "upstream_timeout", 504),
        (httpx.ConnectError, "upstream_unavailable", 502),
        (httpx.ReadTimeout, "upstream_timeout", 504),
    ],
)
@pytest.mark.asyncio
async def test_exhaustion_preserves_final_mapping(failure: Any, code: str, status: int) -> None:
    clock = RetryClock()
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if isinstance(failure, int):
            return httpx.Response(failure)
        raise failure("private-body")

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        with pytest.raises(ApplicationError) as error:
            await RedmineClient(http, "fake", retry_runtime=clock.runtime()).get("issues.json", {})
    assert (error.value.code, error.value.status) == (code, status)
    assert calls == 3 and clock.waits == [0.5, 1.0]


@pytest.mark.parametrize("status", [301, 400, 401, 403, 404, 422, 500])
@pytest.mark.asyncio
async def test_noneligible_status_is_not_replayed(status: int) -> None:
    calls = 0
    clock = RetryClock()

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status, stream=RetryStream(close_failure=None))

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        with pytest.raises(ApplicationError):
            await RedmineClient(http, "fake", retry_runtime=clock.runtime()).get("issues.json", {})
    assert calls == 1 and not clock.waits


@pytest.mark.parametrize("body", [b"invalid-json", b"[]", b'{"x":"too-large"}'])
@pytest.mark.asyncio
async def test_malformed_or_oversized_data_does_not_retry(body: bytes) -> None:
    clock = RetryClock()
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, stream=RetryStream((body,)))

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        with pytest.raises(ApplicationError):
            await RedmineClient(
                http,
                "fake",
                ReadPolicy(max_response_bytes=8 if body == b'{"x":"too-large"}' else 100),
                retry_runtime=clock.runtime(),
            ).get("issues.json", {})
    assert len(requests) == 1 and not clock.waits


@pytest.mark.parametrize(
    "failure", [httpx.PoolTimeout, httpx.LocalProtocolError, httpx.DecodingError]
)
@pytest.mark.asyncio
async def test_noneligible_exception_does_not_retry(failure: Any) -> None:
    clock = RetryClock()
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise failure("private-error")

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        with pytest.raises(ApplicationError):
            await RedmineClient(http, "fake", retry_runtime=clock.runtime()).get("issues.json", {})
    assert calls == 1 and not clock.waits


@pytest.mark.parametrize("headers", [[], ["bad"], ["-1"], ["1.2"], ["1", "2"], ["1, 2"]])
def test_invalid_retry_after_uses_backoff(headers: list[str]) -> None:
    runtime = RetryClock().runtime()
    assert retry_after_seconds(headers, lambda: 0.0) is None
    assert runtime.delay(ReadPolicy(), 1, headers) == 0.5


@pytest.mark.parametrize("seconds", [0, 2, 5, 6])
@pytest.mark.parametrize("as_date", [False, True])
def test_retry_after_and_delay_cap(seconds: int, as_date: bool) -> None:
    now = 1_700_000_000.0
    value = (
        format_datetime(datetime.fromtimestamp(now + seconds, UTC), usegmt=True)
        if as_date
        else str(seconds)
    )
    runtime = RetryRuntime(wall_time=lambda: now, uniform=lambda low, high: high)
    assert runtime.delay(ReadPolicy(), 1, [value]) == (None if seconds > 5 else max(0.5, seconds))
    if as_date:
        assert retry_after_seconds([value + ", " + value], lambda: now) is None


def test_past_dates_huge_headers_and_jitter_bounds() -> None:
    date = format_datetime(datetime.fromtimestamp(1000, UTC), usegmt=True)
    assert retry_after_seconds([date], lambda: 1001) == 0
    assert RetryClock().runtime().delay(ReadPolicy(), 1, ["9" * 1000]) is None
    for number in range(1, 5):
        bound = min(5.0, 0.5 * 2 ** (number - 1))
        for choose in (lambda low, high: low, lambda low, high: high):
            delay = RetryRuntime(uniform=choose).delay(ReadPolicy(), number, [])
            assert delay is not None and bound / 2 <= delay <= bound


@pytest.mark.parametrize(
    "values",
    [
        {"redmine_read_retry_max_attempts": 0},
        {"redmine_read_retry_max_attempts": 6},
        {"redmine_read_retry_base_delay_seconds": 0},
        {"redmine_read_retry_base_delay_seconds": float("nan")},
        {"redmine_read_retry_max_delay_seconds": float("inf")},
        {"redmine_read_retry_base_delay_seconds": 6},
    ],
)
def test_retry_settings_reject_invalid_values(values: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, redmine_url="http://redmine.invalid", **values)


def test_defaults_and_configuration_forwarding() -> None:
    settings = Settings(_env_file=None, redmine_url="http://redmine.invalid")
    assert read_policy(settings) == ReadPolicy()
    settings.redmine_read_retry_max_attempts = 1
    settings.redmine_read_retry_base_delay_seconds = 2
    settings.redmine_read_retry_max_delay_seconds = 4
    policy = read_policy(settings)
    assert (
        policy.retry_max_attempts,
        policy.retry_base_delay_seconds,
        policy.retry_max_delay_seconds,
    ) == (1, 2, 4)
    compose = Path("deploy/compose.yaml").read_text()
    for name, default in (
        ("MAX_ATTEMPTS", "3"),
        ("BASE_DELAY_SECONDS", "0.5"),
        ("MAX_DELAY_SECONDS", "5"),
    ):
        assert (
            compose.count(f"REDMINE_READ_RETRY_{name}: ${{REDMINE_READ_RETRY_{name}:-{default}}}")
            == 2
        )


@pytest.mark.parametrize("reason", ["close-error", "status", "short-deadline", "disabled"])
@pytest.mark.asyncio
async def test_cleanup_and_policy_stop_conditions(reason: str) -> None:
    clock = RetryClock()
    stream = RetryStream(
        close_failure=httpx.ReadError("cleanup") if reason == "close-error" else None
    )
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            503, headers={"Retry-After": "6"} if reason == "status" else {}, stream=stream
        )

    policy = ReadPolicy(
        deadline_seconds=0.1 if reason == "short-deadline" else 60,
        retry_max_attempts=1 if reason == "disabled" else 3,
    )
    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        with pytest.raises(ApplicationError):
            await RedmineClient(http, "fake", policy, retry_runtime=clock.runtime()).get(
                "issues.json", {}
            )
    assert calls == 1 and not clock.waits and stream.closed == 1 and stream.reads == 0


@pytest.mark.asyncio
async def test_retry_releases_permit_and_never_reads_error_body() -> None:
    semaphore = asyncio.Semaphore(1)
    streams: list[RetryStream] = []
    waits: list[float] = []

    def respond(request: httpx.Request) -> httpx.Response:
        stream = RetryStream((b"private-body",))
        streams.append(stream)
        return httpx.Response(503, stream=stream)

    async def sleep(delay: float) -> None:
        assert semaphore._value == 1 and streams[-1].closed == 1
        waits.append(delay)

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=AdmittedTransport(httpx.MockTransport(respond), semaphore, 1),
    ) as http:
        with pytest.raises(ApplicationError):
            await RedmineClient(http, "fake", retry_runtime=RetryRuntime(sleep=sleep)).get(
                "issues.json", {}
            )
    assert len(streams) == 3 and len(waits) == 2
    assert all(stream.closed == 1 and stream.reads == 0 for stream in streams)
    assert semaphore._value == 1


@pytest.mark.parametrize("max_requests", [1, 2, 10])
@pytest.mark.asyncio
async def test_physical_attempts_are_charged_once(max_requests: int) -> None:
    budget = ReadBudget(ReadBudgetPolicy(max_requests=max_requests))
    token = current_budget.set(budget)
    clock = RetryClock()
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, stream=RetryStream())

    try:
        async with httpx.AsyncClient(
            base_url="http://redmine.invalid/",
            transport=AdmittedTransport(httpx.MockTransport(respond), asyncio.Semaphore(1), 1),
        ) as http:
            with pytest.raises(ApplicationError) as error:
                await RedmineClient(http, "fake", retry_runtime=clock.runtime()).get(
                    "issues.json", {}
                )
        assert budget.requests == calls == min(3, max_requests)
        assert error.value.code == (
            "scan_budget_exceeded" if max_requests < 3 else "upstream_unavailable"
        )
    finally:
        current_budget.reset(token)


@pytest.mark.parametrize("max_bytes", [13, 14])
@pytest.mark.asyncio
async def test_partial_tail_is_charged_and_new_attempt_uses_new_buffer(max_bytes: int) -> None:
    streams = [RetryStream((b"bad",), httpx.ReadError("broken")), RetryStream((b'{"ok":true}',))]
    clock = RetryClock()
    budget = ReadBudget(ReadBudgetPolicy(max_bytes=max_bytes))
    token = current_budget.set(budget)
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        stream = streams[calls]
        calls += 1
        return httpx.Response(200, stream=stream)

    try:
        async with httpx.AsyncClient(
            base_url="http://redmine.invalid/",
            transport=AdmittedTransport(httpx.MockTransport(respond), asyncio.Semaphore(1), 1),
        ) as http:
            client = RedmineClient(http, "fake", retry_runtime=clock.runtime())
            if max_bytes == 14:
                assert await client.get("issues.json", {}) == {"ok": True}
            else:
                with pytest.raises(ApplicationError, match="Read byte budget exhausted"):
                    await client.get("issues.json", {})
        assert budget.response_bytes == 14 and budget.requests == calls == 2
        assert all(stream.closed == 1 for stream in streams)
    finally:
        current_budget.reset(token)


@pytest.mark.asyncio
async def test_identity_and_concurrent_callers_retry_with_their_own_keys(caplog: Any) -> None:
    attempts: dict[str, int] = {}
    caplog.set_level(logging.INFO, logger="redmine_mcp.integrations.redmine.client")
    clock = RetryClock()

    def respond(request: httpx.Request) -> httpx.Response:
        key = request.headers["X-Redmine-API-Key"]
        attempts[key] = attempts.get(key, 0) + 1
        if attempts[key] == 1:
            raise httpx.ConnectError("private-exception-detail")
        return httpx.Response(200, json={"user": {"id": 3 if key == "private-key-a" else 8}})

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        readers = [
            RedmineClient(http, key, retry_runtime=clock.runtime())
            for key in ("private-key-a", "private-key-b")
        ]
        values = await asyncio.gather(*(reader.get("users/current.json", {}) for reader in readers))
        identity = RedmineIdentity(http, ReadPolicy(retry_max_attempts=1))
        assert (await identity.current_principal("private-key-a")).redmine_user_id == 3
        service = build_authentication(
            http, Settings(_env_file=None, redmine_url="http://redmine.invalid")
        )
        assert (await service.authenticate("private-key-b")).principal.redmine_user_id == 8
    assert [value["user"]["id"] for value in values] == [3, 8]
    assert attempts == {"private-key-a": 3, "private-key-b": 3}
    assert "ConnectError" in caplog.text
    assert all(
        value not in caplog.text
        for value in ("private-key-a", "private-key-b", "private-exception-detail")
    )


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "binary"])
@pytest.mark.parametrize("failure", [503, httpx.ReadTimeout])
@pytest.mark.asyncio
async def test_mutation_is_never_replayed(method: Any, failure: Any) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if isinstance(failure, int):
            return httpx.Response(failure)
        raise failure("private")

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        writer = RedmineWriter(http, "fake", ReadPolicy(retry_max_attempts=5))
        if method == "binary":
            receipt = await writer.write_binary("uploads.json", b"x", filename="test.txt")
        else:
            receipt = await writer.write_json(method, "issues/7.json")
    assert calls == 1 and receipt.outcome == "uncertain"


@pytest.mark.asyncio
async def test_absolute_budget_cutoff_is_not_reconstructed(monkeypatch: Any) -> None:
    from redmine_mcp.common import read_budget

    clock = RetryClock(now=100)
    monkeypatch.setattr(read_budget, "monotonic", clock.time)
    budget = ReadBudget(ReadBudgetPolicy(deadline_seconds=1), started=100)
    token = current_budget.set(budget)
    calls = 0
    samples = 0

    def now() -> float:
        nonlocal samples
        samples += 1
        # Simulate scheduling between sampling the GET start and consulting its parent.
        if samples == 1:
            clock.now = 100.4
            return 100
        return clock.now

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        clock.now = 100.4 if calls == 1 else 100.95
        return httpx.Response(503 if calls == 1 else 200, json={"ok": True})

    try:
        async with httpx.AsyncClient(
            base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
        ) as http:
            runtime = RetryRuntime(monotonic=now, uniform=lambda low, high: high, sleep=clock.sleep)
            assert await RedmineClient(http, "fake", retry_runtime=runtime).get(
                "issues.json", {}
            ) == {"ok": True}
        assert calls == 2 and budget.deadline == 101
    finally:
        current_budget.reset(token)


@pytest.mark.parametrize("phase", ["stream", "backoff", "admission"])
@pytest.mark.asyncio
async def test_cancellation_stops_dispatch_and_releases_owned_capacity(phase: str) -> None:
    entered = asyncio.Event()
    semaphore = asyncio.Semaphore(0 if phase == "admission" else 1)
    streams: list[RetryStream] = []
    calls = 0

    class BlockingStream(RetryStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            entered.set()
            await asyncio.Event().wait()
            yield b"unreachable"

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        stream = BlockingStream() if phase == "stream" else RetryStream()
        streams.append(stream)
        return httpx.Response(200 if phase == "stream" else 503, stream=stream)

    async def sleep(delay: float) -> None:
        entered.set()
        await asyncio.Event().wait()

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=AdmittedTransport(httpx.MockTransport(respond), semaphore, 1),
    ) as http:
        task = asyncio.create_task(
            RedmineClient(http, "fake", retry_runtime=RetryRuntime(sleep=sleep)).get(
                "issues.json", {}
            )
        )
        if phase == "admission":
            await asyncio.sleep(0)
        else:
            await asyncio.wait_for(entered.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0)
        assert calls == (0 if phase == "admission" else 1)
        assert semaphore._value == (0 if phase == "admission" else 1)
        assert all(stream.closed == 1 for stream in streams)


@pytest.mark.parametrize("aggregate", [False, True])
@pytest.mark.asyncio
async def test_real_acquisition_timeout_preserves_parent_error(aggregate: bool) -> None:
    semaphore = asyncio.Semaphore(1)
    budget = ReadBudget(ReadBudgetPolicy(deadline_seconds=0.02)) if aggregate else None
    token = current_budget.set(budget)
    stream = RetryStream()

    async def respond(request: httpx.Request) -> httpx.Response:
        await asyncio.Event().wait()
        return httpx.Response(200, stream=stream)

    try:
        async with httpx.AsyncClient(
            base_url="http://redmine.invalid/",
            transport=AdmittedTransport(httpx.MockTransport(respond), semaphore, 1),
        ) as http:
            with pytest.raises(ApplicationError) as error:
                await RedmineClient(
                    http, "fake", ReadPolicy(deadline_seconds=1 if aggregate else 0.02)
                ).get("issues.json", {})
        assert error.value.code == ("read_operation_timeout" if aggregate else "upstream_timeout")
        assert semaphore._value == 1
    finally:
        current_budget.reset(token)


@pytest.mark.asyncio
async def test_eof_cleanup_error_does_not_retry_successful_stream() -> None:
    calls = 0
    stream = RetryStream((b"{}",), close_failure=httpx.ReadError("private-cleanup"))
    clock = RetryClock()

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, stream=stream)

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/", transport=httpx.MockTransport(respond)
    ) as http:
        with pytest.raises(ApplicationError):
            await RedmineClient(http, "fake", retry_runtime=clock.runtime()).get("issues.json", {})
    assert calls == 1 and stream.closed == 1 and not clock.waits


@pytest.mark.asyncio
async def test_cancel_during_cleanup_keeps_permit_until_socket_is_closed() -> None:
    entered, finish, closed = asyncio.Event(), asyncio.Event(), asyncio.Event()
    semaphore = asyncio.Semaphore(1)

    class SlowClose(RetryStream):
        async def aclose(self) -> None:
            self.closed += 1
            entered.set()
            await finish.wait()
            closed.set()

    stream = SlowClose()
    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=AdmittedTransport(
            httpx.MockTransport(lambda request: httpx.Response(503, stream=stream)), semaphore, 1
        ),
    ) as http:
        task = asyncio.create_task(RedmineClient(http, "fake").get("issues.json", {}))
        await asyncio.wait_for(entered.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert semaphore._value == 0
        finish.set()
        await asyncio.wait_for(closed.wait(), 1)
        await asyncio.sleep(0)
        assert semaphore._value == 1 and stream.closed == 1


@pytest.mark.asyncio
async def test_capability_parent_timer_stops_child_get_without_replay() -> None:
    from types import SimpleNamespace

    from redmine_mcp.auth.capabilities import CapabilityService

    calls = 0
    semaphore = asyncio.Semaphore(1)

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await asyncio.Event().wait()
        return httpx.Response(200)

    async with httpx.AsyncClient(
        base_url="http://redmine.invalid/",
        transport=AdmittedTransport(httpx.MockTransport(respond), semaphore, 1),
    ) as http:
        reader = RedmineClient(http, "fake")

        async def profile() -> Any:
            return await reader.get("users/current.json", {})

        capabilities = CapabilityService(SimpleNamespace(profile=profile), 3, deadline_seconds=0.02)
        with pytest.raises(ApplicationError) as error:
            await capabilities.candidates(("update_issue",))
        assert error.value.code == "upstream_timeout"
    assert calls == 1 and semaphore._value == 1
