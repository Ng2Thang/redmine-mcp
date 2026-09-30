from dataclasses import dataclass

import httpx

from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.projects.service import ProjectService
from redmine_mcp.features.reference_data.service import ReferenceService
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.issues import RedmineIssues
from redmine_mcp.integrations.redmine.projects import RedmineProjects
from redmine_mcp.integrations.redmine.reference_data import RedmineReferenceData


@dataclass
class Container:
    projects: ProjectService
    issues: IssueService
    reference_data: ReferenceService


def build_container(http: httpx.AsyncClient) -> Container:
    client = RedmineClient(http)
    return Container(
        ProjectService(RedmineProjects(client)),
        IssueService(RedmineIssues(client)),
        ReferenceService(RedmineReferenceData(client)),
    )
