from redmine_mcp.features.users.models import CurrentUser
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import visible_item
from redmine_mcp.integrations.redmine.responses import resource_object


class RedmineUsers:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def get_current_user(self, expected_user_id: int) -> CurrentUser:
        data = await self.client.get("users/current.json", {"include": "memberships"})
        user = resource_object(data.get("user"), expected_user_id)
        # Select only public fields: upstream also returns the current user's API key.
        selected = {
            name: user[name]
            for name in ("id", "login", "firstname", "lastname", "mail", "memberships")
            if name in user
        }
        return visible_item(CurrentUser, selected, observed_fields=("mail",))
