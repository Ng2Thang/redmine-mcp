from typing import Any

from pydantic import ValidationError

from redmine_mcp.common.errors import ApplicationError
from redmine_mcp.common.pagination import Page
from redmine_mcp.features.time_entries.models import IssueTimeEntry
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item


class RedmineTimeEntries:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_issue_time_entries(
        self, issue_id: int, limit: int, offset: int
    ) -> Page[IssueTimeEntry]:
        issue_data = await self.client.get(f"issues/{issue_id}.json", {})
        issue = issue_data.get("issue")
        if (
            not isinstance(issue, dict)
            or type(issue.get("id")) is not int
            or issue["id"] != issue_id
        ):
            raise ApplicationError("upstream_response", "Unexpected Redmine data", 502)

        data = await self.client.get(
            "time_entries.json", {"issue_id": issue_id, "limit": limit, "offset": offset}
        )
        entries = data.get("time_entries")
        total = data.get("total_count")
        if (
            not isinstance(entries, list)
            or type(total) is not int
            or total < 0
            or len(entries) > limit
        ):
            raise ApplicationError("upstream_response", "Unexpected Redmine page", 502)
        if data.get("limit") != limit or data.get("offset") != offset:
            raise ApplicationError("upstream_response", "Unexpected Redmine page", 502)

        mapped = [self._map_entry(entry, issue_id) for entry in entries]
        try:
            return Page[IssueTimeEntry](items=mapped, total=total, limit=limit, offset=offset)
        except ValidationError:
            raise ApplicationError("upstream_response", "Unexpected Redmine page", 502) from None

    @staticmethod
    def _map_entry(entry: Any, issue_id: int) -> IssueTimeEntry:
        if not isinstance(entry, dict):
            raise ApplicationError("upstream_response", "Unexpected Redmine data", 502)
        issue = entry.get("issue")
        if (
            not isinstance(issue, dict)
            or type(issue.get("id")) is not int
            or issue["id"] != issue_id
        ):
            raise ApplicationError("upstream_response", "Unexpected Redmine data", 502)
        return item(
            IssueTimeEntry,
            {
                "id": entry.get("id"),
                "issue_id": issue["id"],
                "user": entry.get("user"),
                "hours": entry.get("hours"),
                "spent_on": entry.get("spent_on"),
            },
        )
