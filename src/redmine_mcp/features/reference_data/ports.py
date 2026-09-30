from typing import Protocol

from redmine_mcp.common.visibility import Collection
from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker


class ReferenceReader(Protocol):
    async def list_issue_statuses(self) -> Collection[IssueStatus]: ...

    async def list_trackers(self) -> Collection[Tracker]: ...

    async def list_issue_priorities(self) -> Collection[IssuePriority]: ...
