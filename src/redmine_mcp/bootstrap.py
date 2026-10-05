from dataclasses import dataclass

import httpx

from redmine_mcp.auth import AuthenticationService
from redmine_mcp.config import Settings
from redmine_mcp.features import (
    AttachmentService,
    IssueService,
    ProjectService,
    ReferenceService,
    TimeEntryService,
    UserService,
)
from redmine_mcp.integrations.redmine import (
    ReadPolicy,
    RedmineAttachmentDeletions,
    RedmineAttachments,
    RedmineAttachmentUpdates,
    RedmineClient,
    RedmineIdentity,
    RedmineIssueCreations,
    RedmineIssueNotes,
    RedmineIssueRelations,
    RedmineIssues,
    RedmineIssueUpdates,
    RedmineProjectFiles,
    RedmineProjects,
    RedmineReferenceData,
    RedmineTimeEntries,
    RedmineUploads,
    RedmineUsers,
    RedmineWriter,
)


@dataclass(frozen=True)
class Container:
    attachments: AttachmentService
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
        max_binary_bytes=settings.redmine_max_binary_bytes,
    )


def build_authentication(
    http: httpx.AsyncClient, settings: Settings | None = None
) -> AuthenticationService:
    return AuthenticationService(RedmineIdentity(http, read_policy(settings)))


def build_container(
    http: httpx.AsyncClient, api_key: str, settings: Settings | None = None
) -> Container:
    client = RedmineClient(http, api_key, read_policy(settings))
    project_reader = RedmineProjects(client)
    writer = RedmineWriter(http, api_key, client.policy)
    attachment_updates = RedmineAttachmentUpdates(client, writer)
    return Container(
        AttachmentService(
            RedmineAttachments(client),
            RedmineUploads(writer, client),
            client.policy.max_binary_bytes,
            metadata_writer=attachment_updates,
            deleter=RedmineAttachmentDeletions(writer, attachment_updates),
        ),
        ProjectService(project_reader, RedmineProjectFiles(writer, project_reader)),
        IssueService(
            RedmineIssues(client),
            RedmineIssueCreations(client, writer),
            updater=RedmineIssueUpdates(client, writer),
            note_updater=RedmineIssueNotes(client, writer),
            relation_creator=RedmineIssueRelations(client, writer),
        ),
        ReferenceService(RedmineReferenceData(client)),
        TimeEntryService(RedmineTimeEntries(client)),
        UserService(RedmineUsers(client)),
    )
