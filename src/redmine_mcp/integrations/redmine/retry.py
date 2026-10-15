"""GET-only retry eligibility and injectable, credential-free delay calculation."""

import asyncio
import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC
from email.utils import parsedate_to_datetime
from random import uniform
from time import monotonic, time

import httpx
from fastapi import status as http_status

from redmine_mcp.integrations.redmine.policy import ReadPolicy

RETRY_STATUSES = frozenset(
    {
        http_status.HTTP_429_TOO_MANY_REQUESTS,
        http_status.HTTP_502_BAD_GATEWAY,
        http_status.HTTP_503_SERVICE_UNAVAILABLE,
        http_status.HTTP_504_GATEWAY_TIMEOUT,
    }
)
RETRY_ERRORS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.WriteError,
    httpx.WriteTimeout,
    httpx.RemoteProtocolError,
)
_HTTP_DATE = re.compile(
    r"(?:[A-Za-z]{3}, [0-9]{2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} GMT"
    r"|[A-Za-z]+, [0-9]{2}-[A-Za-z]{3}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} GMT"
    r"|[A-Za-z]{3} [A-Za-z]{3} (?: [0-9]|[0-9]{2}) [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4})"
)


def retry_reason(failure: httpx.RequestError | None) -> str:
    """Log only names from the fixed allowlist, never exception strings or custom class names."""
    for failure_type in RETRY_ERRORS:
        if isinstance(failure, failure_type):
            return failure_type.__name__
    return "http_status"


def retry_after_seconds(values: Sequence[str], wall_time: Callable[[], float]) -> float | None:
    if len(values) != 1:
        return None
    value = values[0].strip()
    try:
        if re.fullmatch(r"[0-9]+", value):
            # Very large integer headers become infinity and suppress retry at the delay cap.
            return float(value)
        # email.utils accepts trailing text. Require one complete HTTP-date so comma-joined
        # headers or a date followed by another value cannot shorten the requested wait.
        if _HTTP_DATE.fullmatch(value) is None:
            return None
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        return max(0.0, date.timestamp() - wall_time())
    except (ValueError, OverflowError, OSError, TypeError):
        return None


@dataclass(frozen=True)
class RetryRuntime:
    monotonic: Callable[[], float] = monotonic
    wall_time: Callable[[], float] = time
    uniform: Callable[[float, float], float] = uniform
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep

    def delay(
        self, policy: ReadPolicy, retry_number: int, header_values: Sequence[str]
    ) -> float | None:
        bound = min(
            policy.retry_max_delay_seconds,
            policy.retry_base_delay_seconds * 2 ** (retry_number - 1),
        )
        backoff = self.uniform(bound / 2, bound)
        header_delay = retry_after_seconds(header_values, self.wall_time)
        if header_delay is None:
            return backoff
        if header_delay > policy.retry_max_delay_seconds:
            return None
        return max(backoff, header_delay)
