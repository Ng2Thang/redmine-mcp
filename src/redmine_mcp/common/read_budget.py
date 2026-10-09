"""An operation-local read budget, never a user quota or persistent query state."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from time import monotonic

from fastapi import status as http_status

from redmine_mcp.common.errors import ApplicationError
from redmine_mcp.constants import logs as logs_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReadBudgetPolicy:
    max_requests: int = 30
    max_bytes: int = 10 * 1024 * 1024
    deadline_seconds: float = 90


MEMBERSHIP_BATCH_DEFAULTS = ReadBudgetPolicy(
    max_requests=300, max_bytes=30 * 1024 * 1024, deadline_seconds=300
)


@dataclass
class ReadBudget:
    policy: ReadBudgetPolicy
    requests: int = 0
    response_bytes: int = 0
    started: float = field(default_factory=monotonic)

    @property
    def deadline(self) -> float:
        return self.started + self.policy.deadline_seconds

    def check_deadline(self) -> None:
        if monotonic() >= self.deadline:
            logger.debug(logs_text.BUDGET_EXHAUSTED, "deadline", self.requests, self.response_bytes)
            raise ApplicationError(
                "read_operation_timeout",
                "Read operation timed out; narrow the scope",
                http_status.HTTP_504_GATEWAY_TIMEOUT,
            )

    def check_request_available(self) -> None:
        self.check_deadline()
        if self.requests >= self.policy.max_requests:
            logger.debug(logs_text.BUDGET_EXHAUSTED, "requests", self.requests, self.response_bytes)
            raise ApplicationError(
                "scan_budget_exceeded",
                "Read request budget exhausted; narrow the scope",
                http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

    def request(self) -> None:
        self.check_request_available()
        self.requests += 1

    def consume(self, size: int) -> None:
        self.check_deadline()
        self.response_bytes += size
        if self.response_bytes > self.policy.max_bytes:
            logger.debug(logs_text.BUDGET_EXHAUSTED, "bytes", self.requests, self.response_bytes)
            raise ApplicationError(
                "scan_budget_exceeded",
                "Read byte budget exhausted; narrow the scope",
                http_status.HTTP_422_UNPROCESSABLE_CONTENT,
            )


current_budget: ContextVar[ReadBudget | None] = ContextVar("redmine_read_budget", default=None)


def charge_request() -> None:
    budget = current_budget.get()
    if budget is not None:
        budget.request()


def charge_bytes(size: int) -> None:
    budget = current_budget.get()
    if budget is not None:
        budget.consume(size)


def check_read_deadline() -> None:
    budget = current_budget.get()
    if budget is not None:
        budget.check_deadline()


def check_read_request_available() -> None:
    """Check retry admission without charging a second physical request."""
    budget = current_budget.get()
    if budget is not None:
        budget.check_request_available()


def read_deadline() -> float | None:
    """Expose the absolute monotonic cutoff without restarting a cooperative batch timer."""
    budget = current_budget.get()
    if budget is None:
        return None
    budget.check_deadline()
    return budget.deadline


@asynccontextmanager
async def read_operation(policy: ReadBudgetPolicy, *, fresh: bool = False) -> AsyncIterator[None]:
    if not fresh and current_budget.get() is not None:
        yield
        return
    budget = ReadBudget(policy)
    token = current_budget.set(budget)
    try:
        logger.debug(
            logs_text.BUDGET_STARTED, policy.max_requests, policy.max_bytes, policy.deadline_seconds
        )
        try:
            async with asyncio.timeout(policy.deadline_seconds):
                yield
                check_read_deadline()
        except TimeoutError:
            logger.debug(
                logs_text.BUDGET_EXHAUSTED, "deadline", budget.requests, budget.response_bytes
            )
            raise ApplicationError(
                "read_operation_timeout",
                "Read operation timed out; narrow the scope",
                http_status.HTTP_504_GATEWAY_TIMEOUT,
            ) from None
    finally:
        try:
            logger.debug(
                logs_text.BUDGET_COMPLETED,
                budget.requests,
                budget.response_bytes,
                (monotonic() - budget.started) * 1000,
            )
        finally:
            current_budget.reset(token)
