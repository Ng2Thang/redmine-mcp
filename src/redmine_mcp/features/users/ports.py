from typing import Protocol

from redmine_mcp.features.users.models import CurrentUser


class UserReader(Protocol):
    async def get_current_user(self, expected_user_id: int) -> CurrentUser: ...
