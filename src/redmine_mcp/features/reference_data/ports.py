from typing import Protocol

from redmine_mcp.common import Collection
from redmine_mcp.features.reference_data.models import (
    DocumentCategory,
    IssuePriority,
    IssueStatus,
    Tracker,
)


class ReferenceReader(Protocol):
    async def list_issue_statuses(self) -> Collection[IssueStatus]: ...

    async def list_trackers(self) -> Collection[Tracker]: ...

    async def list_issue_priorities(self) -> Collection[IssuePriority]: ...

    async def list_document_categories(self) -> Collection[DocumentCategory]: ...
