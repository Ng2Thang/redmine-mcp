from typing import cast

from fastapi import Request

from redmine_mcp.bootstrap import Container
from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.projects.service import ProjectService
from redmine_mcp.features.reference_data.service import ReferenceService
from redmine_mcp.features.time_entries.service import TimeEntryService


def get_projects(request: Request) -> ProjectService:
    return cast(Container, request.app.state.container).projects


def get_issues(request: Request) -> IssueService:
    return cast(Container, request.app.state.container).issues


def get_reference_data(request: Request) -> ReferenceService:
    return cast(Container, request.app.state.container).reference_data


def get_time_entries(request: Request) -> TimeEntryService:
    return cast(Container, request.app.state.container).time_entries
