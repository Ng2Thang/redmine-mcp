from hashlib import sha256
from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi import status as http_status
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader

from redmine_mcp.api.runtime import get_settings, get_upstream
from redmine_mcp.auth import (
    READ_OPERATIONS,
    WRITE_OPERATIONS,
    AuthContext,
    AuthorizationPolicy,
    normalize_api_key,
)
from redmine_mcp.bootstrap import build_authentication
from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import auth as auth_text

policy = AuthorizationPolicy(READ_OPERATIONS, WRITE_OPERATIONS)
api_key_header = APIKeyHeader(name="X-Redmine-API-Key", auto_error=False)


async def get_auth_context(
    request: Request, key: Annotated[str | None, Depends(api_key_header)]
) -> AuthContext:
    keys = request.headers.getlist("x-redmine-api-key")
    if len(keys) != 1 or key is None:
        raise HTTPException(http_status.HTTP_401_UNAUTHORIZED, auth_text.INVALID_API_KEY)
    try:
        api_key = normalize_api_key(key)
        settings = get_settings(request)
        if settings.redmine_write_enabled and not compare_digest(
            sha256(api_key.encode("ascii")).hexdigest(), settings.redmine_writer_key_sha256
        ):
            raise HTTPException(http_status.HTTP_401_UNAUTHORIZED, auth_text.INVALID_API_KEY)
        service = build_authentication(get_upstream(request), settings)
        context = await service.authenticate(api_key)
        if settings.redmine_write_enabled and (
            context.principal.redmine_user_id not in settings.writer_user_ids
        ):
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
        return context
    except ApplicationError as exc:
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
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
    policy.authorize(context.principal, f"read:{route.operation_id}")


def require_mcp_access(context: Annotated[AuthContext, Depends(get_auth_context)]) -> None:
    policy.authorize(context.principal, "mcp:connect")


def require_write_access(
    request: Request,
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> None:
    settings = get_settings(request)
    if not settings.redmine_write_enabled:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.WRITE_ACCESS_DISABLED)
    route = request.scope.get("route")
    if not isinstance(route, APIRoute) or not route.operation_id:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
    if route.operation_id not in settings.writer_operations:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, auth_text.PERMISSION_DENIED)
    policy.authorize(context.principal, f"write:{route.operation_id}")
