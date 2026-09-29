from typing import cast

from fastapi import Request

from redmine_mcp.bootstrap import Container
from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.projects.service import ProjectService


def get_projects(request: Request) -> ProjectService:
    return cast(Container, request.app.state.container).projects


def get_issues(request: Request) -> IssueService:
    return cast(Container, request.app.state.container).issues
