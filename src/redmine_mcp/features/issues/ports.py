from datetime import datetime
from typing import Protocol

from redmine_mcp.common import Page
from redmine_mcp.features.issues.models import Issue, IssueDetail
from redmine_mcp.features.issues.write_models import (
    IssueCreateRequest,
    IssueCreateResult,
    IssueNoteUpdateRequest,
    IssueNoteUpdateResult,
    IssueRelationCreateRequest,
    IssueRelationCreateResult,
    IssueUpdateRequest,
    IssueUpdateResult,
)


class IssueReader(Protocol):
    async def list_issues(
        self,
        project_id: int | None,
        status_id: str,
        assigned_to_id: str | None,
        limit: int,
        offset: int,
        tracker_id: int | None,
        parent_id: int | None,
        updated_since: datetime | None,
        sort: str,
        category_id: int | None,
        fixed_version_id: int | None,
        include_subprojects: bool,
        include: tuple[str, ...] | None,
    ) -> Page[Issue]: ...

    async def get_issue(
        self, issue_id: int, include: tuple[str, ...] | None = None
    ) -> IssueDetail: ...


class IssueCreator(Protocol):
    async def create_issue(self, request: IssueCreateRequest) -> IssueCreateResult: ...


class IssueUpdater(Protocol):
    async def update_issue(
        self, issue_id: int, request: IssueUpdateRequest
    ) -> IssueUpdateResult: ...


class IssueNoteUpdater(Protocol):
    async def update_issue_note(
        self, issue_id: int, journal_id: int, request: IssueNoteUpdateRequest
    ) -> IssueNoteUpdateResult: ...


class IssueRelationCreator(Protocol):
    async def create_issue_relation(
        self, issue_id: int, request: IssueRelationCreateRequest
    ) -> IssueRelationCreateResult: ...
