"""An operation-local read budget, never a user quota or persistent query state."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from time import monotonic

from redmine_mcp.common.errors import ApplicationError


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

    def check_deadline(self) -> None:
        if monotonic() - self.started >= self.policy.deadline_seconds:
            raise ApplicationError(
                "read_operation_timeout", "Read operation timed out; narrow the scope", 504
            )

    def request(self) -> None:
        self.check_deadline()
        if self.requests >= self.policy.max_requests:
            raise ApplicationError(
                "scan_budget_exceeded", "Read request budget exhausted; narrow the scope", 422
            )
        self.requests += 1

    def consume(self, size: int) -> None:
        self.check_deadline()
        self.response_bytes += size
        if self.response_bytes > self.policy.max_bytes:
            raise ApplicationError(
                "scan_budget_exceeded", "Read byte budget exhausted; narrow the scope", 422
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


@asynccontextmanager
async def read_operation(policy: ReadBudgetPolicy, *, fresh: bool = False) -> AsyncIterator[None]:
    if not fresh and current_budget.get() is not None:
        yield
        return
    token = current_budget.set(ReadBudget(policy))
    try:
        try:
            async with asyncio.timeout(policy.deadline_seconds):
                yield
                check_read_deadline()
        except TimeoutError:
            raise ApplicationError(
                "read_operation_timeout", "Read operation timed out; narrow the scope", 504
            ) from None
    finally:
        current_budget.reset(token)
