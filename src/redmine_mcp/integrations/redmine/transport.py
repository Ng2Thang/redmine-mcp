"""Shared, credential-free HTTP transport configuration."""

import asyncio
from collections.abc import AsyncIterator

import httpx
from httpx._utils import get_environment_proxies

from redmine_mcp.common import ApplicationError
from redmine_mcp.common.read_budget import charge_request
from redmine_mcp.config import Settings


class AdmittedStream(httpx.AsyncByteStream):
    def __init__(self, stream: httpx.AsyncByteStream, semaphore: asyncio.Semaphore) -> None:
        self.stream = stream
        self.semaphore = semaphore
        self.close_task: asyncio.Task[None] | None = None

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self.stream:
            yield chunk

    async def aclose(self) -> None:
        if self.close_task is None:
            self.close_task = asyncio.create_task(self._close())
            self.close_task.add_done_callback(self._observe_close)
        # Cancellation of a caller must not cancel socket cleanup or release the
        # permit while the underlying response is still being closed.
        await asyncio.shield(self.close_task)

    @staticmethod
    def _observe_close(task: asyncio.Task[None]) -> None:
        if not task.cancelled():
            task.exception()

    async def _close(self) -> None:
        try:
            await self.stream.aclose()
        finally:
            self.semaphore.release()


class AdmittedTransport(httpx.AsyncBaseTransport):
    """One permit per physical request, held until its response stream closes."""

    def __init__(
        self,
        inner: httpx.AsyncBaseTransport,
        semaphore: asyncio.Semaphore,
        admission_seconds: float,
    ) -> None:
        self.inner = inner
        self.semaphore = semaphore
        self.admission_seconds = admission_seconds

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        request.extensions["redmine_dispatched"] = False
        charge_request()
        try:
            async with asyncio.timeout(self.admission_seconds):
                await self.semaphore.acquire()
        except TimeoutError:
            raise ApplicationError(
                "upstream_busy", "Redmine request capacity is busy; retry later", 503
            ) from None
        try:
            request.extensions["redmine_dispatched"] = True
            response = await self.inner.handle_async_request(request)
            if not isinstance(response.stream, httpx.AsyncByteStream):
                raise RuntimeError("Unexpected upstream stream")
            response.stream = AdmittedStream(response.stream, self.semaphore)
            return response
        except BaseException:
            self.semaphore.release()
            raise

    async def aclose(self) -> None:
        await self.inner.aclose()


def create_upstream_client(settings: Settings) -> httpx.AsyncClient:
    semaphore = asyncio.Semaphore(settings.redmine_max_concurrent_requests)
    limits = httpx.Limits(
        max_connections=settings.redmine_max_connections,
        max_keepalive_connections=settings.redmine_max_keepalive_connections,
    )

    def admitted_transport(proxy: str | None = None) -> AdmittedTransport:
        return AdmittedTransport(
            httpx.AsyncHTTPTransport(limits=limits, retries=0, proxy=proxy),
            semaphore,
            settings.redmine_admission_timeout_seconds,
        )

    # A custom transport disables HTTPX's automatic environment proxy mounts.
    # Reuse its parser to retain platform proxy and NO_PROXY matching semantics.
    # Every proxy pool shares the direct transport's admission semaphore.
    mounts: dict[str, httpx.AsyncBaseTransport | None] = {
        pattern: None if proxy is None else admitted_transport(proxy)
        for pattern, proxy in get_environment_proxies().items()
    }
    return httpx.AsyncClient(
        base_url=str(settings.redmine_url).rstrip("/") + "/",
        timeout=httpx.Timeout(
            settings.redmine_timeout_seconds,
            connect=settings.redmine_connect_timeout_seconds,
            pool=settings.redmine_pool_timeout_seconds,
        ),
        transport=admitted_transport(),
        mounts=mounts,
        follow_redirects=False,
    )
