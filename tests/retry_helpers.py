"""Deterministic retry timing and observable response streams for offline tests."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from time import monotonic

import httpx

from redmine_mcp.integrations.redmine.retry import RetryRuntime


@dataclass
class RetryClock:
    now: float = field(default_factory=monotonic)
    waits: list[float] = field(default_factory=list)

    def time(self) -> float:
        return self.now

    async def sleep(self, delay: float) -> None:
        self.waits.append(delay)
        self.now += delay
        await asyncio.sleep(0)

    def runtime(self) -> RetryRuntime:
        return RetryRuntime(monotonic=self.time, uniform=lambda low, high: high, sleep=self.sleep)


class RetryStream(httpx.AsyncByteStream):
    def __init__(
        self,
        chunks: tuple[bytes, ...] = (),
        failure: Exception | None = None,
        close_failure: Exception | None = None,
    ) -> None:
        self.chunks = chunks
        self.failure = failure
        self.close_failure = close_failure
        self.closed = 0
        self.reads = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self.chunks:
            self.reads += 1
            yield chunk
        if self.failure is not None:
            raise self.failure

    async def aclose(self) -> None:
        self.closed += 1
        if self.close_failure is not None:
            raise self.close_failure
