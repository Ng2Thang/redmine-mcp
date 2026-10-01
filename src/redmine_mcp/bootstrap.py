from dataclasses import dataclass

import httpx

from redmine_mcp.auth import AuthenticationService
from redmine_mcp.config import Settings
from redmine_mcp.features import (
    IssueService,
    ProjectService,
    ReferenceService,
    TimeEntryService,
    UserService,
)
from redmine_mcp.integrations.redmine import (
    ReadPolicy,
    RedmineClient,
    RedmineIdentity,
    RedmineIssues,
    RedmineProjects,
    RedmineReferenceData,
    RedmineTimeEntries,
    RedmineUsers,
)


@dataclass(frozen=True)
class Container:
    projects: ProjectService
    issues: IssueService
    reference_data: ReferenceService
    time_entries: TimeEntryService
    users: UserService


def read_policy(settings: Settings | None) -> ReadPolicy:
    if settings is None:
        return ReadPolicy()
    return ReadPolicy(
        deadline_seconds=settings.redmine_request_deadline_seconds,
        max_response_bytes=settings.redmine_max_response_bytes,
    )


def build_authentication(
    http: httpx.AsyncClient, settings: Settings | None = None
) -> AuthenticationService:
    return AuthenticationService(RedmineIdentity(http, read_policy(settings)))


def build_container(
    http: httpx.AsyncClient, api_key: str, settings: Settings | None = None
) -> Container:
    client = RedmineClient(http, api_key, read_policy(settings))
    return Container(
        ProjectService(RedmineProjects(client)),
        IssueService(RedmineIssues(client)),
        ReferenceService(RedmineReferenceData(client)),
        TimeEntryService(RedmineTimeEntries(client)),
        UserService(RedmineUsers(client)),
    )
