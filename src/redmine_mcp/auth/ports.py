from typing import Protocol

from redmine_mcp.auth.models import Principal


class IdentityReader(Protocol):
    async def current_principal(self, api_key: str) -> Principal: ...
