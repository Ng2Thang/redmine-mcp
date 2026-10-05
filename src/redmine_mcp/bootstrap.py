from dataclasses import dataclass

import httpx

from redmine_mcp.auth import AuthenticationService
from redmine_mcp.auth.capabilities import CapabilityService
from redmine_mcp.auth.models import Principal
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
    RedmineIssueWatchers,
    RedmineProjectFiles,
    RedmineProjects,
    RedmineReferenceData,
    RedmineTimeEntries,
    RedmineUploads,
    RedmineUsers,
    RedmineWriter,
)
from redmine_mcp.integrations.redmine.capabilities import RedmineCapabilities


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
    http: httpx.AsyncClient,
    api_key: str,
    settings: Settings | None = None,
    principal: Principal | None = None,
) -> Container:
    client = RedmineClient(http, api_key, read_policy(settings))
    project_reader = RedmineProjects(client)
    writer = RedmineWriter(http, api_key, client.policy)
    attachment_updates = RedmineAttachmentUpdates(client, writer)
    authorizer = (
        build_capabilities(http, api_key, settings, principal)
        if settings is not None and settings.personal_writer
        else None
    )
    return Container(
        AttachmentService(
            RedmineAttachments(client),
            RedmineUploads(writer, client),
            client.policy.max_binary_bytes,
            metadata_writer=attachment_updates,
            deleter=RedmineAttachmentDeletions(writer, attachment_updates),
            authorizer=authorizer,
        ),
        ProjectService(
            project_reader, RedmineProjectFiles(writer, project_reader), authorizer=authorizer
        ),
        IssueService(
            RedmineIssues(client),
            RedmineIssueCreations(client, writer),
            updater=RedmineIssueUpdates(client, writer),
            note_updater=RedmineIssueNotes(client, writer),
            relation_creator=RedmineIssueRelations(client, writer),
            relation_deleter=RedmineIssueRelations(client, writer),
            watcher_adder=RedmineIssueWatchers(client, writer),
            watcher_remover=RedmineIssueWatchers(client, writer),
            authorizer=authorizer,
        ),
        ReferenceService(RedmineReferenceData(client)),
        TimeEntryService(RedmineTimeEntries(client)),
        UserService(RedmineUsers(client)),
    )


def build_capabilities(
    http: httpx.AsyncClient,
    api_key: str,
    settings: Settings | None = None,
    principal: Principal | None = None,
) -> CapabilityService:
    client = RedmineClient(http, api_key, read_policy(settings))
    containers = RedmineAttachmentUpdates(client, RedmineWriter(http, api_key, client.policy))
    return CapabilityService(
        RedmineCapabilities(client, containers),
        principal.redmine_user_id if principal is not None else None,
        client.policy.deadline_seconds,
    )
