from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import collection


class RedmineReferenceData:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_issue_statuses(self) -> list[IssueStatus]:
        data = await self.client.get("issue_statuses.json", {})
        return collection(IssueStatus, data, "issue_statuses")

    async def list_trackers(self) -> list[Tracker]:
        data = await self.client.get("trackers.json", {})
        return collection(Tracker, data, "trackers")

    async def list_issue_priorities(self) -> list[IssuePriority]:
        data = await self.client.get("enumerations/issue_priorities.json", {})
        return collection(IssuePriority, data, "issue_priorities")
