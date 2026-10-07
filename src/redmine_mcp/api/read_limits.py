"""Budget REST readers before authentication, including internal MCP requests."""

import re

from fastapi import status as http_status
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from redmine_mcp.api.error_handlers import application_error
from redmine_mcp.common import ApplicationError
from redmine_mcp.common.read_budget import ReadBudgetPolicy, check_read_deadline, read_operation


class ReadLimitsMiddleware:
    def __init__(self, app: ASGIApp, policy: ReadBudgetPolicy) -> None:
        self.app = app
        self.policy = policy

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope["path"]
        if re.fullmatch(r"/api/v1/attachments/[^/]+/content/?", path):
            response = await application_error(
                Request(scope),
                ApplicationError(
                    "attachment_download_disabled",
                    "Use attachment metadata and its Redmine link",
                    http_status.HTTP_403_FORBIDDEN,
                ),
            )
            await response(scope, receive, send)
            return
        if scope["method"] != "GET" or not path.startswith("/api/v1/"):
            await self.app(scope, receive, send)
            return
        started = False
        deadline_error: ApplicationError | None = None

        async def guarded_send(message: Message) -> None:
            nonlocal started, deadline_error
            if deadline_error is not None:
                return
            if message["type"] == "http.response.start":
                try:
                    check_read_deadline()
                except ApplicationError as exc:
                    # Inner exception middleware already considers headers sent.
                    # Discard this response and report the error at our boundary.
                    deadline_error = exc
                    return
                started = True
            await send(message)

        try:
            async with read_operation(self.policy):
                await self.app(scope, receive, guarded_send)
                if deadline_error is not None:
                    raise deadline_error
        except ApplicationError as exc:
            if started:
                raise RuntimeError("Read response interrupted") from None
            response = await application_error(Request(scope), exc)
            await response(scope, receive, send)
