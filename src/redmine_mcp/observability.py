import logging
import re
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import PurePath
from time import perf_counter
from uuid import uuid4

from redmine_mcp.constants import logs as logs_text

request_id: ContextVar[str] = ContextVar("request_id", default="-")
call_id: ContextVar[str] = ContextVar("call_id", default="-")
_VENDOR_LOGGERS = ("httpx", "httpcore", "fastapi_mcp", "mcp")

# Match only application-owned endpoint shapes; never echo unrecognized path segments.
_ENDPOINTS = (
    "users/current.json",
    "issues.json",
    "projects.json",
    "roles.json",
    "time_entries.json",
    "issue_statuses.json",
    "trackers.json",
    "uploads.json",
    "enumerations/issue_priorities.json",
    "enumerations/document_categories.json",
    "issues/{id}.json",
    "projects/{id}.json",
    "roles/{id}.json",
    "users/{id}.json",
    "memberships/{id}.json",
    "attachments/{id}.json",
    "versions/{id}.json",
    "relations/{id}.json",
    "time_entries/{id}.json",
    "journals/{id}.json",
    "projects/{id}/versions.json",
    "projects/{id}/issue_categories.json",
    "projects/{id}/files.json",
    "projects/{id}/time_entry_activities.json",
    "projects/{id}/memberships.json",
    "issues/{id}/relations.json",
    "issues/{id}/watchers.json",
    "issues/{id}/watchers/{id}.json",
)
_ENDPOINT_PATTERNS = tuple(
    (re.compile(re.escape(template).replace(r"\{id\}", r"[0-9]+")), template)
    for template in _ENDPOINTS
)


def endpoint_template(path: str) -> str:
    return next(
        (template for pattern, template in _ENDPOINT_PATTERNS if pattern.fullmatch(path)),
        "unknown",
    )


def safe_operation(value: object) -> str:
    # Lazy import avoids the configuration/authentication dependency cycle.
    from redmine_mcp.auth.policy import READ_OPERATIONS, WRITE_OPERATIONS

    return (
        value
        if isinstance(value, str) and value in (*READ_OPERATIONS, *WRITE_OPERATIONS)
        else "unknown"
    )


def debug_exception(logger: logging.Logger, exc: BaseException) -> None:
    """Inspect code locations only; never format exception values or source/locals."""
    if not logger.isEnabledFor(logging.DEBUG):
        return
    frames: deque[str] = deque(maxlen=20)
    traceback = exc.__traceback__
    count = 0
    while traceback is not None:
        code = traceback.tb_frame.f_code
        # Restrict text from dynamically compiled code to ordinary code identifiers.
        filename = PurePath(code.co_filename).name
        filename = filename if re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", filename) else "unknown"
        function = code.co_name
        function = function if re.fullmatch(r"[A-Za-z0-9_<>.]{1,100}", function) else "unknown"
        frames.append(f"{filename}:{function}:{traceback.tb_lineno}")
        count += 1
        traceback = traceback.tb_next
    logger.debug(logs_text.ERROR_STACK, ",".join(frames) or "-", count > 20)


@dataclass
class CallOutcome:
    value: str = "completed"


@contextmanager
def logical_call(operation: str, correlation: str | None) -> Iterator[CallOutcome]:
    """Bind each SDK invocation independently of the long-lived session task."""
    logger = logging.getLogger("redmine_mcp.calls")
    request_token = request_id.set(
        correlation if correlation and re.fullmatch(r"[0-9a-f]{32}", correlation) else uuid4().hex
    )
    call_token = call_id.set(uuid4().hex)
    started = perf_counter()
    outcome = CallOutcome()
    try:
        logger.debug(logs_text.CALL_STARTED, operation)
        yield outcome
    except BaseException as exc:
        outcome.value = "interrupted" if not isinstance(exc, Exception) else "failed"
        debug_exception(logger, exc)
        raise
    finally:
        try:
            logger.debug(
                logs_text.CALL_COMPLETED,
                operation,
                outcome.value,
                (perf_counter() - started) * 1000,
            )
        finally:
            call_id.reset(call_token)
            request_id.reset(request_token)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        record.call_id = call_id.get()
        if any(
            record.name == name or record.name.startswith(name + ".") for name in _VENDOR_LOGGERS
        ):
            # Vendor WARNING/ERROR events may interpolate payloads or format raw exceptions.
            record.msg = logs_text.VENDOR_DIAGNOSTIC
            record.args = ()
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=logging.INFO if level.upper() == "DEBUG" else level.upper(),
        format=logs_text.LOG_FORMAT,
    )
    logging.getLogger().setLevel(logging.INFO if level.upper() == "DEBUG" else level.upper())
    logging.getLogger("redmine_mcp").setLevel(level.upper())
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(logging.Formatter(logs_text.LOG_FORMAT))
        if not any(isinstance(entry, RequestContextFilter) for entry in handler.filters):
            handler.addFilter(RequestContextFilter())
    for name in _VENDOR_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger(__name__).debug(logs_text.LOGGING_CONFIGURED, level.upper())
