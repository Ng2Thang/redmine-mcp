from redmine_mcp.common import Page
from redmine_mcp.features.time_entries import IssueTimeEntry
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item
from redmine_mcp.integrations.redmine.responses import resource_object, response_page


class RedmineTimeEntries:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_issue_time_entries(
        self, issue_id: int, limit: int, offset: int
    ) -> Page[IssueTimeEntry]:
        issue_data = await self.client.get(f"issues/{issue_id}.json", {})
        resource_object(issue_data.get("issue"), issue_id)

        data = await self.client.get(
            "time_entries.json", {"issue_id": issue_id, "limit": limit, "offset": offset}
        )
        envelope = response_page(data, "time_entries", limit, offset, require_metadata=True)
        return Page[IssueTimeEntry](
            items=[self._map_entry(entry, issue_id) for entry in envelope.items],
            total=envelope.total,
            limit=envelope.limit,
            offset=envelope.offset,
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
