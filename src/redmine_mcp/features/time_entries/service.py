from datetime import date

from redmine_mcp.auth.capability_models import WriteIntent
from redmine_mcp.auth.capability_ports import WriteAuthorizer
from redmine_mcp.common import Page, PageRequest, require_positive_id, validated_query
from redmine_mcp.features.time_entries.models import IssueTimeEntry, TimeEntry
from redmine_mcp.features.time_entries.ports import (
    TimeEntryCreator,
    TimeEntryDeleter,
    TimeEntryReader,
    TimeEntryUpdater,
)
from redmine_mcp.features.time_entries.queries import TimeEntrySearch, TimeEntryUserId
from redmine_mcp.features.time_entries.write_models import (
    TimeEntryCreateRequest,
    TimeEntryCreateResult,
    TimeEntryDeleteResult,
    TimeEntryUpdateRequest,
    TimeEntryUpdateResult,
)


class TimeEntryService:
    def __init__(
        self,
        reader: TimeEntryReader,
        *,
        creator: TimeEntryCreator | None = None,
        updater: TimeEntryUpdater | None = None,
        deleter: TimeEntryDeleter | None = None,
        authorizer: WriteAuthorizer | None = None,
        caller_id: int | None = None,
    ) -> None:
        self.reader = reader
        self.creator = creator
        self.updater = updater
        self.deleter = deleter
        self.authorizer = authorizer
        self.caller_id = caller_id

    async def create_time_entry(
        self, issue_id: int, request: TimeEntryCreateRequest
    ) -> TimeEntryCreateResult:
        require_positive_id(issue_id, "issue_id")
        if self.creator is None or self.caller_id is None:
            raise RuntimeError("Time-entry creator or authenticated caller is not configured")
        require_positive_id(self.caller_id, "caller_id")
        if self.authorizer is not None:
            await self.authorizer.authorize(WriteIntent("create_time_entry", issue_id=issue_id))
        return await self.creator.create_time_entry(issue_id, request, self.caller_id)

    async def update_time_entry(
        self, issue_id: int, time_entry_id: int, request: TimeEntryUpdateRequest
    ) -> TimeEntryUpdateResult:
        require_positive_id(issue_id, "issue_id")
        require_positive_id(time_entry_id, "time_entry_id")
        if self.updater is None or self.caller_id is None:
            raise RuntimeError("Time-entry updater or authenticated caller is not configured")
        require_positive_id(self.caller_id, "caller_id")
        if self.authorizer is not None:
            await self.authorizer.authorize(
                WriteIntent("update_time_entry", issue_id=issue_id, time_entry_id=time_entry_id)
            )
        return await self.updater.update_time_entry(issue_id, time_entry_id, request)

    async def delete_time_entry(self, issue_id: int, time_entry_id: int) -> TimeEntryDeleteResult:
        require_positive_id(issue_id, "issue_id")
        require_positive_id(time_entry_id, "time_entry_id")
        if self.deleter is None or self.caller_id is None:
            raise RuntimeError("Time-entry deleter or authenticated caller is not configured")
        require_positive_id(self.caller_id, "caller_id")
        if self.authorizer is not None:
            await self.authorizer.authorize(
                WriteIntent("delete_time_entry", issue_id=issue_id, time_entry_id=time_entry_id)
            )
        return await self.deleter.delete_time_entry(issue_id, time_entry_id)

    async def list_time_entries(
        self,
        project_id: int | None = None,
        include_subprojects: bool = False,
        user_id: TimeEntryUserId | None = None,
        issue_id: int | None = None,
        spent_from: date | None = None,
        spent_to: date | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> Page[TimeEntry]:
        query = validated_query(
            TimeEntrySearch,
            {
                "project_id": project_id,
                "include_subprojects": include_subprojects,
                "user_id": user_id,
                "issue_id": issue_id,
                "spent_from": spent_from,
                "spent_to": spent_to,
                "limit": limit,
                "offset": offset,
            },
        )
        return await self.reader.list_time_entries(
            project_id=query.project_id,
            include_subprojects=query.include_subprojects,
            user_id=query.user_id,
            issue_id=query.issue_id,
            spent_from=query.spent_from,
            spent_to=query.spent_to,
            limit=query.limit,
            offset=query.offset,
        )

    async def list_issue_time_entries(
        self, issue_id: int, limit: int = 25, offset: int = 0
    ) -> Page[IssueTimeEntry]:
        require_positive_id(issue_id, "issue_id")
        query = validated_query(PageRequest, {"limit": limit, "offset": offset})
        return await self.reader.list_issue_time_entries(
            issue_id=issue_id, limit=query.limit, offset=query.offset
        )
