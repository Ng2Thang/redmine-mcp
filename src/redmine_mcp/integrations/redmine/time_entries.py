from datetime import date

from redmine_mcp.common import Page
from redmine_mcp.features.time_entries import IssueTimeEntry
from redmine_mcp.features.time_entries.models import TimeEntry, TimeEntryIssueReference
from redmine_mcp.features.time_entries.queries import TimeEntryUserId
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item
from redmine_mcp.integrations.redmine.responses import resource_object, response_page


class RedmineTimeEntries:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_time_entries(
        self,
        project_id: int | None,
        include_subprojects: bool,
        user_id: TimeEntryUserId | None,
        issue_id: int | None,
        spent_from: date | None,
        spent_to: date | None,
        limit: int,
        offset: int,
    ) -> Page[TimeEntry]:
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
            "sort": "spent_on:asc",
        }
        if project_id is not None:
            params["project_id"] = project_id
            params["subproject_id"] = "*" if include_subprojects else "!*"
        if user_id is not None:
            params["user_id"] = user_id
        if issue_id is not None:
            params["issue_id"] = issue_id
        if spent_from is not None:
            params["from"] = spent_from.isoformat()
        if spent_to is not None:
            params["to"] = spent_to.isoformat()
        guidance = (
            "Narrow time-entry filters by project, credited user, issue or spent_on date range; "
            "this query requires too many pages"
        )
        data = await self.client.get_page(
            "time_entries.json", "time_entries", params, guidance, require_metadata=True
        )
        envelope = response_page(data, "time_entries", limit, offset, require_metadata=True)
        return Page[TimeEntry](
            items=[self._map_time_entry(entry) for entry in envelope.items],
            total=envelope.total,
            limit=envelope.limit,
            offset=envelope.offset,
            pagination_policy=self.client.pagination.describe(envelope.total, limit),
        )

    @staticmethod
    def _map_time_entry(entry: dict[str, object]) -> TimeEntry:
        issue = entry.get("issue")
        issue_id = item(TimeEntryIssueReference, issue).id if issue is not None else None
        return item(
            TimeEntry,
            {
                "id": entry.get("id"),
                "project": entry.get("project"),
                "user": entry.get("user"),
                "issue_id": issue_id,
                "hours": entry.get("hours"),
                "spent_on": entry.get("spent_on"),
                "activity": entry.get("activity"),
                "comments": entry.get("comments"),
            },
        )

    async def list_issue_time_entries(
        self, issue_id: int, limit: int, offset: int
    ) -> Page[IssueTimeEntry]:
        guidance = (
            "Select an issue with fewer time entries; this tool has no date filter "
            "and the query requires too many pages"
        )
        self.client.pagination.check_depth(limit, offset, guidance)
        issue_data = await self.client.get(f"issues/{issue_id}.json", {})
        resource_object(issue_data.get("issue"), issue_id)

        data = await self.client.get_page(
            "time_entries.json",
            "time_entries",
            {"issue_id": issue_id, "limit": limit, "offset": offset},
            guidance,
            require_metadata=True,
        )
        envelope = response_page(data, "time_entries", limit, offset, require_metadata=True)
        return Page[IssueTimeEntry](
            items=[self._map_entry(entry, issue_id) for entry in envelope.items],
            total=envelope.total,
            limit=envelope.limit,
            offset=envelope.offset,
            pagination_policy=self.client.pagination.describe(envelope.total, limit),
        )

    @staticmethod
    def _map_entry(entry: dict[str, object], issue_id: int) -> IssueTimeEntry:
        issue = resource_object(entry.get("issue"), issue_id)
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
