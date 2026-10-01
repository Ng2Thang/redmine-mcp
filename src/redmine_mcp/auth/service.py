from fastapi import status as http_status

from redmine_mcp.auth.models import AuthContext
from redmine_mcp.auth.ports import IdentityReader
from redmine_mcp.common import ApplicationError


def normalize_api_key(value: str) -> str:
    key = value.strip()
    if (
        not key
        or len(value) > 512
        or any(ord(character) < 33 or ord(character) > 126 for character in key)
    ):
        raise ApplicationError(
            "invalid_credentials",
            "Missing or invalid Redmine API key",
            http_status.HTTP_401_UNAUTHORIZED,
        )
    return key


class AuthenticationService:
    def __init__(self, reader: IdentityReader) -> None:
        self.reader = reader

    async def authenticate(self, api_key: str) -> AuthContext:
        key = normalize_api_key(api_key)
        try:
            principal = await self.reader.current_principal(key)
        except ApplicationError as exc:
            if exc.status in (http_status.HTTP_401_UNAUTHORIZED, http_status.HTTP_403_FORBIDDEN):
                raise ApplicationError(
                    "invalid_credentials",
                    "Missing or invalid Redmine API key",
                    http_status.HTTP_401_UNAUTHORIZED,
                ) from None
            raise
        return AuthContext(principal, key)
