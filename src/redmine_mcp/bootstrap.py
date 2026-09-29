from dataclasses import dataclass

import httpx

from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.projects.service import ProjectService
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.issues import RedmineIssues
from redmine_mcp.integrations.redmine.projects import RedmineProjects


@dataclass
class Container:
    projects: ProjectService
    issues: IssueService


def build_container(http: httpx.AsyncClient) -> Container:
    client = RedmineClient(http)
    return Container(ProjectService(RedmineProjects(client)), IssueService(RedmineIssues(client)))
