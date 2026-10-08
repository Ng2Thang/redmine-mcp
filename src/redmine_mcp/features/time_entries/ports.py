from datetime import date
from typing import Protocol

from redmine_mcp.common import Page
from redmine_mcp.features.time_entries.models import IssueTimeEntry, TimeEntry
from redmine_mcp.features.time_entries.queries import TimeEntryUserId
from redmine_mcp.features.time_entries.write_models import (
    TimeEntryCreateRequest,
    TimeEntryCreateResult,
)


class TimeEntryReader(Protocol):
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
    ) -> Page[TimeEntry]: ...

    async def list_issue_time_entries(
        self, issue_id: int, limit: int, offset: int
    ) -> Page[IssueTimeEntry]: ...


class TimeEntryCreator(Protocol):
    async def create_time_entry(
        self, issue_id: int, request: TimeEntryCreateRequest, caller_id: int
    ) -> TimeEntryCreateResult: ...
