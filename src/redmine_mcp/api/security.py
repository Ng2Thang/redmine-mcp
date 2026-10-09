import logging
from hashlib import sha256
from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi import status as http_status
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken

from redmine_mcp.api.runtime import get_settings, get_upstream
from redmine_mcp.auth import (
    READ_OPERATIONS,
    WRITE_OPERATIONS,
    AuthContext,
    AuthorizationPolicy,
    normalize_api_key,
)
from redmine_mcp.bootstrap import build_authentication, read_budget_policy
from redmine_mcp.common import ApplicationError
from redmine_mcp.common.read_budget import read_operation
from redmine_mcp.constants import auth as auth_text
from redmine_mcp.constants import logs as logs_text
from redmine_mcp.observability import debug_exception, safe_operation

logger = logging.getLogger(__name__)

policy = AuthorizationPolicy(READ_OPERATIONS, WRITE_OPERATIONS)
api_key_header = APIKeyHeader(name="X-Redmine-API-Key", auto_error=False)


async def get_auth_context(
    request: Request, key: Annotated[str | None, Depends(api_key_header)]
) -> AuthContext:
    keys = request.headers.getlist("x-redmine-api-key")
    if len(keys) != 1 or key is None:
        logger.debug(logs_text.AUTHENTICATION, "denied", "header_cardinality")
        raise HTTPException(http_status.HTTP_401_UNAUTHORIZED, auth_text.INVALID_API_KEY)
    try:
        api_key = normalize_api_key(key)
        settings = get_settings(request)
        pinned_writer = settings.redmine_write_enabled and not settings.personal_writer
        if pinned_writer and not compare_digest(
            sha256(api_key.encode("ascii")).hexdigest(), settings.redmine_writer_key_sha256
        ):
            logger.debug(logs_text.AUTHENTICATION, "denied", "pinned_key")
            raise HTTPException(http_status.HTTP_401_UNAUTHORIZED, auth_text.INVALID_API_KEY)
        service = build_authentication(get_upstream(request), settings)
        async with read_operation(
            read_budget_policy(settings), fresh=not request.url.path.startswith("/api/v1/")
        ):
            context = await service.authenticate(api_key)
        if pinned_writer and (context.principal.redmine_user_id not in settings.writer_user_ids):
            logger.debug(logs_text.AUTHENTICATION, "denied", "writer_user_gate")
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
        logger.debug(logs_text.AUTHENTICATION, "authenticated", "identity_verified")
        return context
    except ApplicationError as exc:
        logger.debug(logs_text.AUTHENTICATION, "failed", "identity_or_input")
        debug_exception(logger, exc)
        if exc.status in (http_status.HTTP_401_UNAUTHORIZED, http_status.HTTP_403_FORBIDDEN):
            raise HTTPException(
                http_status.HTTP_401_UNAUTHORIZED, auth_text.INVALID_API_KEY
            ) from None
        raise


def require_read_access(
    request: Request, context: Annotated[AuthContext, Depends(get_auth_context)]
) -> None:
    route = request.scope.get("route")
    if not isinstance(route, APIRoute) or not route.operation_id:
        logger.debug(logs_text.AUTHORIZATION, "unknown", "denied", "unrecognized_route")
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
    policy.authorize(context.principal, f"read:{route.operation_id}")


def require_mcp_access(
    request: Request, context: Annotated[AuthContext, Depends(get_auth_context)]
) -> None:
    policy.authorize(context.principal, "mcp:connect")
    # The SDK owns session binding and cleanup. Never put the raw key in its token object.
    request.state.auth_context = context
    request.scope["user"] = AuthenticatedUser(
        AccessToken(
            token="",
            client_id=f"redmine:{context.principal.redmine_user_id}",
            subject=sha256(context.api_key.encode("ascii")).hexdigest(),
            scopes=[],
            claims={"iss": str(get_settings(request).redmine_url)},
        )
    )


def require_write_access(
    request: Request,
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> None:
    settings = get_settings(request)
    if not settings.redmine_write_enabled:
        logger.debug(logs_text.AUTHORIZATION, "unknown", "denied", "writer_disabled")
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.WRITE_ACCESS_DISABLED)
    if (
        settings.personal_writer
        and settings.writer_user_ids
        and (context.principal.redmine_user_id not in settings.writer_user_ids)
    ):
        logger.debug(logs_text.AUTHORIZATION, "unknown", "denied", "writer_user_gate")
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
    route = request.scope.get("route")
    if not isinstance(route, APIRoute) or not route.operation_id:
        logger.debug(logs_text.AUTHORIZATION, "unknown", "denied", "unrecognized_route")
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
    if route.operation_id not in settings.writer_operations:
        logger.debug(
            logs_text.AUTHORIZATION, safe_operation(route.operation_id), "denied", "operation_gate"
        )
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
    policy.authorize(context.principal, f"write:{route.operation_id}")
