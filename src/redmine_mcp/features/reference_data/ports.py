from typing import Protocol

from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker


class ReferenceReader(Protocol):
    async def list_issue_statuses(self) -> list[IssueStatus]: ...

    async def list_trackers(self) -> list[Tracker]: ...

    async def list_issue_priorities(self) -> list[IssuePriority]: ...
