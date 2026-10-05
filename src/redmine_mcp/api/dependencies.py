from typing import Annotated

from fastapi import Depends, Request

from redmine_mcp.api.runtime import get_settings, get_upstream
from redmine_mcp.api.security import get_auth_context
from redmine_mcp.auth import AuthContext
from redmine_mcp.bootstrap import Container, build_container
from redmine_mcp.features import (
    AttachmentService,
    IssueService,
    ProjectService,
    ReferenceService,
    TimeEntryService,
    UserService,
)


def get_container(
    request: Request, context: Annotated[AuthContext, Depends(get_auth_context)]
) -> Container:
    return build_container(
        get_upstream(request), context.api_key, get_settings(request), context.principal
    )


def get_projects(container: Annotated[Container, Depends(get_container)]) -> ProjectService:
    return container.projects


def get_attachments(container: Annotated[Container, Depends(get_container)]) -> AttachmentService:
    return container.attachments


def get_issues(container: Annotated[Container, Depends(get_container)]) -> IssueService:
    return container.issues


def get_reference_data(container: Annotated[Container, Depends(get_container)]) -> ReferenceService:
    return container.reference_data


def get_time_entries(container: Annotated[Container, Depends(get_container)]) -> TimeEntryService:
    return container.time_entries


def get_users(container: Annotated[Container, Depends(get_container)]) -> UserService:
    return container.users
