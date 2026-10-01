import httpx
from fastapi import status as http_status

from redmine_mcp.auth import Principal
from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.responses import response_object


class RedmineIdentity:
    def __init__(self, http: httpx.AsyncClient, policy: ReadPolicy) -> None:
        self.http = http
        self.policy = policy

    async def current_principal(self, api_key: str) -> Principal:
        data = await RedmineClient(self.http, api_key, self.policy).get("users/current.json", {})
        user = response_object(data.get("user"))
        user_id = user.get("id")
        if type(user_id) is not int or user_id < 1:
            raise ApplicationError(
                codes_text.UPSTREAM_RESPONSE,
                redmine_text.INVALID_RESPONSE,
                http_status.HTTP_502_BAD_GATEWAY,
            )
        return Principal(user_id)
