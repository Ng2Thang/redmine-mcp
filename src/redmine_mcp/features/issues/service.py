from datetime import datetime

from redmine_mcp.common import Page, require_positive_id, validated_query
from redmine_mcp.features.issues.models import Issue, IssueDetail
from redmine_mcp.features.issues.ports import (
    IssueCreator,
    IssueNoteUpdater,
    IssueReader,
    IssueUpdater,
)
from redmine_mcp.features.issues.queries import (
    IssueSearch,
    validate_issue_includes,
    validate_issue_list_includes,
)
from redmine_mcp.features.issues.write_models import (
    IssueCreateRequest,
    IssueCreateResult,
    IssueNoteUpdateRequest,
    IssueNoteUpdateResult,
    IssueUpdateRequest,
    IssueUpdateResult,
)


class IssueService:
    def __init__(
        self,
        reader: IssueReader,
        creator: IssueCreator | None = None,
        updater: IssueUpdater | None = None,
        note_updater: IssueNoteUpdater | None = None,
    ) -> None:
        self.reader = reader
        self.creator = creator
        self.updater = updater
        self.note_updater = note_updater

    async def create_issue(self, request: IssueCreateRequest) -> IssueCreateResult:
        require_positive_id(request.project_id, "project_id")
        if self.creator is None:
            raise RuntimeError("Issue creator is not configured")
        return await self.creator.create_issue(request)

    async def update_issue(self, issue_id: int, request: IssueUpdateRequest) -> IssueUpdateResult:
        require_positive_id(issue_id, "issue_id")
        if self.updater is None:
            raise RuntimeError("Issue updater is not configured")
        return await self.updater.update_issue(issue_id, request)

    async def update_issue_note(
        self, issue_id: int, journal_id: int, request: IssueNoteUpdateRequest
    ) -> IssueNoteUpdateResult:
        require_positive_id(issue_id, "issue_id")
        require_positive_id(journal_id, "journal_id")
        if self.note_updater is None:
            raise RuntimeError("Issue note updater is not configured")
        return await self.note_updater.update_issue_note(issue_id, journal_id, request)

    async def list_issues(
        self,
        project_id: int | None = None,
        status_id: str = "open",
        assigned_to_id: str | None = None,
        limit: int = 25,
        offset: int = 0,
        tracker_id: int | None = None,
        parent_id: int | None = None,
        updated_since: datetime | None = None,
        sort: str = "id:asc",
        category_id: int | None = None,
        fixed_version_id: int | None = None,
        include_subprojects: bool = True,
        include: tuple[str, ...] | None = None,
    ) -> Page[Issue]:
        query = validated_query(
            IssueSearch,
            {
                "project_id": project_id,
                "status_id": status_id,
                "assigned_to_id": assigned_to_id,
                "limit": limit,
                "offset": offset,
                "tracker_id": tracker_id,
                "parent_id": parent_id,
                "updated_since": updated_since,
                "sort": sort,
                "category_id": category_id,
                "fixed_version_id": fixed_version_id,
                "include_subprojects": include_subprojects,
            },
        )
        return await self.reader.list_issues(
            project_id=query.project_id,
            status_id=query.status_id,
            assigned_to_id=query.assigned_to_id,
            limit=query.limit,
            offset=query.offset,
            tracker_id=query.tracker_id,
            parent_id=query.parent_id,
            updated_since=query.updated_since,
            sort=query.sort,
            category_id=query.category_id,
            fixed_version_id=query.fixed_version_id,
            include_subprojects=query.include_subprojects,
            include=validate_issue_list_includes(include),
        )

    async def get_issue(self, issue_id: int, include: tuple[str, ...] | None = None) -> IssueDetail:
        require_positive_id(issue_id, "issue_id")
        return await self.reader.get_issue(issue_id, validate_issue_includes(include))
