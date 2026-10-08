from dataclasses import dataclass

import httpx

from redmine_mcp.auth import WRITE_OPERATIONS, AuthenticationService
from redmine_mcp.auth.capabilities import CapabilityService
from redmine_mcp.auth.models import Principal
from redmine_mcp.common.read_budget import MEMBERSHIP_BATCH_DEFAULTS, ReadBudgetPolicy
from redmine_mcp.config import Settings
from redmine_mcp.features import (
    AttachmentService,
    IssueService,
    ProjectService,
    ReferenceService,
    TimeEntryService,
    UserService,
)
from redmine_mcp.features.projects.membership_service import ProjectMembershipService
from redmine_mcp.features.users.capability_service import ProjectCapabilityService
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
    RedmineProjectVersions,
    RedmineReferenceData,
    RedmineTimeEntries,
    RedmineTimeEntryCreations,
    RedmineTimeEntryUpdates,
    RedmineUploads,
    RedmineUsers,
    RedmineWriter,
)
from redmine_mcp.integrations.redmine.capabilities import RedmineCapabilities
from redmine_mcp.integrations.redmine.project_memberships import RedmineProjectMemberships


@dataclass(frozen=True)
class Container:
    attachments: AttachmentService
    projects: ProjectService
    issues: IssueService
    reference_data: ReferenceService
    time_entries: TimeEntryService
    users: UserService
    project_capabilities: ProjectCapabilityService | None = None
    project_members: ProjectMembershipService | None = None


def read_policy(settings: Settings | None) -> ReadPolicy:
    if settings is None:
        return ReadPolicy()
    return ReadPolicy(
        deadline_seconds=settings.redmine_request_deadline_seconds,
        max_response_bytes=settings.redmine_max_response_bytes,
        max_binary_bytes=settings.redmine_max_binary_bytes,
        max_query_pages=settings.redmine_max_query_pages,
        public_url=str(settings.redmine_public_url) if settings.redmine_public_url else None,
        retry_max_attempts=settings.redmine_read_retry_max_attempts,
        retry_base_delay_seconds=settings.redmine_read_retry_base_delay_seconds,
        retry_max_delay_seconds=settings.redmine_read_retry_max_delay_seconds,
    )


def read_budget_policy(settings: Settings) -> ReadBudgetPolicy:
    return ReadBudgetPolicy(
        max_requests=settings.redmine_read_operation_max_requests,
        max_bytes=settings.redmine_read_operation_max_bytes,
        deadline_seconds=settings.redmine_read_operation_deadline_seconds,
    )


def membership_batch_policy(settings: Settings | None) -> ReadBudgetPolicy:
    if settings is None:
        return MEMBERSHIP_BATCH_DEFAULTS
    return ReadBudgetPolicy(
        max_requests=settings.redmine_membership_batch_max_requests,
        max_bytes=settings.redmine_membership_batch_max_read_bytes,
        deadline_seconds=settings.redmine_membership_batch_deadline_seconds,
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
    admitted = settings is not None and settings.redmine_write_enabled and principal is not None
    if admitted and settings is not None and principal is not None:
        admitted = not settings.writer_user_ids or (
            principal.redmine_user_id in settings.writer_user_ids
        )
    operations = tuple(
        operation
        for operation in WRITE_OPERATIONS
        if admitted and settings is not None and operation in settings.writer_operations
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
            project_reader,
            RedmineProjectFiles(writer, project_reader),
            authorizer=authorizer,
            version_creator=RedmineProjectVersions(client, writer),
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
        TimeEntryService(
            RedmineTimeEntries(client),
            creator=RedmineTimeEntryCreations(client, writer),
            updater=RedmineTimeEntryUpdates(client, writer),
            authorizer=authorizer,
            caller_id=principal.redmine_user_id if principal is not None else None,
        ),
        UserService(RedmineUsers(client)),
        ProjectCapabilityService(
            project_reader,
            build_capabilities(http, api_key, settings, principal),
            operations,
            max_query_pages=client.policy.max_query_pages,
        ),
        ProjectMembershipService(
            RedmineProjectMemberships(client, writer),
            build_capabilities(http, api_key, settings, principal),
            budget_policy=membership_batch_policy(settings),
        ),
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
