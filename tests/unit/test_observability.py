"""G04: console configuration, safe identifiers, bounded stacks and context teardown."""

import asyncio
import logging
import re
import sys
from typing import Any

import pytest

from redmine_mcp import observability as obs
from tests.logging_helpers import Console
from tests.logging_helpers import console as console

SECRET = "sensitive-SENTINEL-83f17"


def test_log_levels_reconfigure_without_duplicate_handlers_or_filters(console: Console) -> None:
    logger = logging.getLogger("redmine_mcp.test")
    initial_handlers = logging.getLogger().handlers[:]
    for level in ("INFO", "DEBUG", "DEBUG", "INFO", "debug", "WARNING"):
        obs.configure_logging(level)
        console.clear()
        logger.debug("debug-control")
        logger.info("info-control")
        logger.warning("warning-control")
        assert (
            "debug-control" in console.output.getvalue()
            if level.upper() == "DEBUG"
            else ("debug-control" not in console.output.getvalue())
        )
        assert len(console.records) == {"INFO": 2, "DEBUG": 3, "WARNING": 1}[level.upper()]
        assert logging.getLogger().handlers == initial_handlers
        assert len([f for f in console.filters if isinstance(f, obs.RequestContextFilter)]) == 1
        assert all(r.request_id == r.call_id == "-" for r in console.records)
        assert logging.getLogger().level == (
            logging.WARNING if level == "WARNING" else logging.INFO
        )
        assert all(logging.getLogger(n).level == logging.WARNING for n in obs._VENDOR_LOGGERS)


@pytest.mark.parametrize("vendor", ["httpx", "httpcore.connection", "fastapi_mcp", "mcp.server"])
@pytest.mark.parametrize("level", [logging.WARNING, logging.ERROR])
def test_vendor_console_removes_arguments_cached_exceptions_and_stack(
    console: Console, vendor: str, level: int
) -> None:
    obs.configure_logging("DEBUG")
    try:
        raise ValueError(SECRET)
    except ValueError:
        record = logging.LogRecord(vendor, level, SECRET, 1, "%s", (SECRET,), sys.exc_info())
    record.exc_text = SECRET
    record.stack_info = SECRET
    console.handle(record)
    text = console.output.getvalue()
    assert SECRET not in text
    assert "vendor_diagnostic details_omitted=true" in text
    assert record.args == () and record.exc_info is record.exc_text is record.stack_info is None


@pytest.mark.parametrize(
    "path,expected",
    [
        ("issues/123.json", "issues/{id}.json"),
        ("issues/12/watchers/8.json", "issues/{id}/watchers/{id}.json"),
        ("projects/6/files.json", "projects/{id}/files.json"),
        ("issues.json", "issues.json"),
        (f"issues/{SECRET}.json", "unknown"),
        ("issues/12.json?key=secret", "unknown"),
        ("https://host.invalid/issues.json", "unknown"),
        ("/issues.json", "unknown"),
    ],
)
def test_endpoint_templates_never_echo_unknown_input(path: str, expected: str) -> None:
    assert obs.endpoint_template(path) == expected


@pytest.mark.parametrize("value", [None, 42, {}, SECRET, "download_attachment", "list_tools"])
def test_unknown_operations_are_placeholders(value: Any) -> None:
    assert obs.safe_operation(value) == "unknown"


def test_registered_read_and_write_operations_are_retained() -> None:
    from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS

    for operation in (*READ_OPERATIONS, *WRITE_OPERATIONS):
        assert obs.safe_operation(operation) == operation


@pytest.mark.parametrize("depth,truncated", [(0, False), (30, True)])
def test_exception_console_has_only_bounded_code_locations(
    console: Console, depth: int, truncated: bool
) -> None:
    obs.configure_logging("DEBUG")

    def fail(remaining: int) -> None:
        secret_local = SECRET
        if remaining:
            fail(remaining - 1)
        raise ValueError(secret_local)

    try:
        fail(depth)
    except ValueError as error:
        obs.debug_exception(logging.getLogger("redmine_mcp.test"), error)
    record = console.records[-1]
    frames, actual_truncated = record.args
    assert actual_truncated is truncated
    assert 1 <= len(frames.split(",")) <= 20
    assert all(
        re.fullmatch(r"[A-Za-z0-9_.-]+:[A-Za-z0-9_<>.]+:[0-9]+", f) for f in frames.split(",")
    )
    assert SECRET not in console.output.getvalue()
    assert "raise ValueError" not in console.output.getvalue()


def test_dynamic_code_locations_are_sanitized(console: Console) -> None:
    obs.configure_logging("DEBUG")
    try:
        exec(compile("raise ValueError('private-value')", "unsafe secret /bad filename", "exec"))
    except ValueError as error:
        obs.debug_exception(logging.getLogger("redmine_mcp.test"), error)
    assert "unknown:<module>:1" in console.output.getvalue()
    assert "unsafe secret" not in console.output.getvalue()
    assert "private-value" not in console.output.getvalue()


def test_info_does_not_inspect_traceback(console: Console) -> None:
    obs.configure_logging("INFO")

    class Uninspectable:
        @property
        def __traceback__(self) -> Any:
            raise AssertionError("INFO must not inspect a stack")

    obs.debug_exception(logging.getLogger("redmine_mcp.test"), Uninspectable())
    assert not console.records


@pytest.mark.parametrize("failure", [None, ValueError, asyncio.CancelledError])
@pytest.mark.parametrize("correlation", ["b" * 32, SECRET, None])
def test_nested_call_context_restores_parent_on_completion_failure_and_cancel(
    console: Console, failure: Any, correlation: str | None
) -> None:
    obs.configure_logging("DEBUG")
    with obs.logical_call("list_issues", "a" * 32):
        parent = obs.request_id.get(), obs.call_id.get()
        try:
            with obs.logical_call("get_issue", correlation):
                assert obs.call_id.get() != parent[1]
                assert re.fullmatch("[0-9a-f]{32}", obs.call_id.get())
                assert (
                    obs.request_id.get() == correlation
                    if correlation == "b" * 32
                    else (re.fullmatch("[0-9a-f]{32}", obs.request_id.get()))
                )
                if failure:
                    raise failure(SECRET)
        except (ValueError, asyncio.CancelledError):
            pass
        assert (obs.request_id.get(), obs.call_id.get()) == parent
    assert obs.request_id.get() == obs.call_id.get() == "-"
    completed = [r for r in console.records if r.getMessage().startswith("mcp_call_completed")]
    expected = (
        "completed" if failure is None else "failed" if failure is ValueError else "interrupted"
    )
    assert f"outcome={expected}" in completed[0].getMessage()
    assert SECRET not in console.output.getvalue()
