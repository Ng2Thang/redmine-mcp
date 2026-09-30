from redmine_mcp.common.visibility import Collection
from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import wrapped_collection


class RedmineReferenceData:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_issue_statuses(self) -> Collection[IssueStatus]:
        data = await self.client.get("issue_statuses.json", {})
        return wrapped_collection(IssueStatus, data, "issue_statuses")

    async def list_trackers(self) -> Collection[Tracker]:
        data = await self.client.get("trackers.json", {})
        return wrapped_collection(Tracker, data, "trackers")

    async def list_issue_priorities(self) -> Collection[IssuePriority]:
        data = await self.client.get("enumerations/issue_priorities.json", {})
        return wrapped_collection(IssuePriority, data, "issue_priorities")
