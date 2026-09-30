from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker
from redmine_mcp.features.reference_data.ports import ReferenceReader


class ReferenceService:
    def __init__(self, reader: ReferenceReader) -> None:
        self.reader = reader

    async def list_issue_statuses(self) -> list[IssueStatus]:
        return await self.reader.list_issue_statuses()

    async def list_trackers(self) -> list[Tracker]:
        return await self.reader.list_trackers()

    async def list_issue_priorities(self) -> list[IssuePriority]:
        return await self.reader.list_issue_priorities()
