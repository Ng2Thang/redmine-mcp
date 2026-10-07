"""BODY-024: admission before downstream parsing, authentication and dispatch."""

import asyncio
from typing import Any

import pytest
from pydantic import ValidationError

from redmine_mcp.api.body_limits import RequestBodyLimitsMiddleware
from redmine_mcp.config import Settings

pytestmark = pytest.mark.asyncio


async def probe(chunks, headers=(), path="/mcp", method="POST", cap=4):
    messages = list(chunks)
    sent = []
    received = []
    calls = []

    async def receive():
        message = messages.pop(0) if messages else {"type": "http.disconnect"}
        received.append(message)
        return message

    async def send(message):
        sent.append(message)

    async def downstream(scope, replay, send):
        calls.append(await replay())
        calls.append(await replay())

    scope: dict[str, Any] = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": list(headers),
        "query_string": b"",
        "state": {},
    }
    await RequestBodyLimitsMiddleware(downstream, cap)(scope, receive, send)
    status = next((m["status"] for m in sent if m["type"] == "http.response.start"), None)
    return status, calls, received, sent


@pytest.mark.parametrize("path", ["/mcp", "/mcp/", "/api/v1/issues/42"])
@pytest.mark.parametrize("declared", [False, True])
async def test_oversize_never_dispatches(path, declared):
    headers = [(b"content-length", b"5")] if declared else []
    status, calls, received, sent = await probe(
        [{"type": "http.request", "body": b"abcde"}], headers, path=path
    )
    assert status == 413 and calls == []
    assert len(received) == (0 if declared else 1)
    assert b"abcde" not in b"".join(m.get("body", b"") for m in sent)


@pytest.mark.parametrize(
    "length,status",
    [
        (None, None),
        (b"4", None),
        (b"004, 4", None),
        (b"3", 400),
        (b"-1", 400),
        (b"4,5", 400),
        (b"+4", 400),
        (b"", 400),
        (b"9" * 5000, 413),
    ],
)
async def test_framing_and_exact_cap(length, status):
    headers = [] if length is None else [(b"content-length", length)]
    result, calls, _, _ = await probe(
        [
            {"type": "http.request", "body": b"ab", "more_body": True},
            {"type": "http.request", "body": b"cd", "more_body": False},
        ],
        headers,
    )
    assert result == status
    assert calls == (
        [{"type": "http.request", "body": b"abcd", "more_body": False}, {"type": "http.disconnect"}]
        if status is None
        else []
    )


async def test_duplicate_lengths_and_understated_stream():
    status, calls, _, _ = await probe(
        [{"type": "http.request", "body": b"abcd"}],
        [(b"content-length", b"04"), (b"Content-Length", b"4")],
    )
    assert status is None and calls[0]["body"] == b"abcd"
    status, calls, received, _ = await probe(
        [
            {"type": "http.request", "body": b"abcd", "more_body": True},
            {"type": "http.request", "body": b"e", "more_body": True},
            {"type": "http.request", "body": b"unused"},
        ],
        [(b"content-length", b"1")],
    )
    assert status == 413 and not calls and len(received) == 2


@pytest.mark.parametrize("encoding", [b"gzip", b"br", b"identity,gzip", b""])
async def test_encoding_rejected_without_receive(encoding):
    status, calls, received, _ = await probe([], [(b"content-encoding", encoding)])
    assert status == 415 and not calls and not received


async def test_identity_encoding_and_partial_disconnect():
    status, calls, _, _ = await probe(
        [{"type": "http.request", "body": b"x"}], [(b"content-encoding", b" IDENTITY ")]
    )
    assert status is None and calls[0]["body"] == b"x"
    status, calls, _, _ = await probe(
        [
            {"type": "http.request", "body": b"x", "more_body": True},
            {"type": "http.disconnect"},
        ]
    )
    assert status is None and not calls


@pytest.mark.parametrize(
    "path,method",
    [("/mcp", "GET"), ("/mcp", "DELETE"), ("/api/v1/issues", "GET"), ("/health", "POST")],
)
async def test_unlimited_channels_pass_through(path, method):
    status, calls, _, _ = await probe(
        [{"type": "http.request", "body": b"unbounded", "more_body": True}],
        [(b"content-length", b"999")],
        path,
        method,
    )
    assert status is None and calls[0]["body"] == b"unbounded"


async def test_receive_cancellation_propagates_without_dispatch():
    calls = []

    async def receive():
        raise asyncio.CancelledError

    async def app(*args):
        calls.append(args)

    with pytest.raises(asyncio.CancelledError):
        await RequestBodyLimitsMiddleware(app, 4)(
            {"type": "http", "path": "/mcp", "method": "POST", "headers": []},
            receive,
            app,
        )
    assert not calls


async def test_derived_cap_and_invalid_configuration():
    settings = Settings(_env_file=None, redmine_url="http://redmine.invalid")
    assert settings.effective_max_request_body_bytes >= (
        4 * ((settings.redmine_max_binary_bytes + 2) // 3) + 65536
    )
    assert (
        Settings(
            _env_file=None, redmine_url="http://redmine.invalid", redmine_max_request_body_bytes=123
        ).effective_max_request_body_bytes
        == 123
    )
    for value in (0, -1):
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                redmine_url="http://redmine.invalid",
                redmine_max_request_body_bytes=value,
            )
