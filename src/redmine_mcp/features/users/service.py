from redmine_mcp.features.users.models import CurrentUser
from redmine_mcp.features.users.ports import UserReader


class UserService:
    def __init__(self, reader: UserReader) -> None:
        self.reader = reader

    async def get_current_user(self, expected_user_id: int) -> CurrentUser:
        return await self.reader.get_current_user(expected_user_id)
