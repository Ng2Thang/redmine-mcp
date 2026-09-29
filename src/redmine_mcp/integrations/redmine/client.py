from typing import Any

import httpx

from redmine_mcp.common.errors import ApplicationError


class RedmineClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self.http = http

    async def get(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        try:
            response = await self.http.get(path, params=params)
        except httpx.TimeoutException:
            raise ApplicationError("upstream_timeout", "Redmine timed out", 504) from None
        except httpx.RequestError:
            raise ApplicationError("upstream_unavailable", "Cannot reach Redmine", 502) from None
        if response.status_code == 401:
            raise ApplicationError("upstream_authentication", "Redmine credential rejected", 502)
        if response.status_code == 403:
            raise ApplicationError("access_denied", "Redmine access denied", 403)
        if response.status_code == 404:
            raise ApplicationError("resource_not_found", "Resource unavailable or not visible", 404)
        if response.status_code >= 300:
            raise ApplicationError("upstream_error", "Redmine request failed", 502)
        try:
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError
            return result
        except ValueError:
            raise ApplicationError("upstream_response", "Invalid Redmine response", 502) from None
