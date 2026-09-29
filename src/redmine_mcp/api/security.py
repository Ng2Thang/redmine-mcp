import secrets
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from redmine_mcp.config import Settings

bearer = HTTPBearer(auto_error=False)


def require_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> None:
    settings = cast(Settings, request.app.state.settings)
    if credentials is None or not secrets.compare_digest(
        credentials.credentials.encode(), settings.mcp_api_token.get_secret_value().encode()
    ):
        raise HTTPException(
            401, "Missing or invalid MCP token", headers={"WWW-Authenticate": "Bearer"}
        )
