from dataclasses import dataclass

import httpx

from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.projects.service import ProjectService
from redmine_mcp.features.reference_data.service import ReferenceService
from redmine_mcp.features.time_entries.service import TimeEntryService
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.issues import RedmineIssues
from redmine_mcp.integrations.redmine.projects import RedmineProjects
from redmine_mcp.integrations.redmine.reference_data import RedmineReferenceData
from redmine_mcp.integrations.redmine.time_entries import RedmineTimeEntries


@dataclass
class Container:
    projects: ProjectService
    issues: IssueService
    reference_data: ReferenceService
    time_entries: TimeEntryService


def build_container(http: httpx.AsyncClient) -> Container:
    client = RedmineClient(http)
    return Container(
        ProjectService(RedmineProjects(client)),
        IssueService(RedmineIssues(client)),
        ReferenceService(RedmineReferenceData(client)),
        TimeEntryService(RedmineTimeEntries(client)),
    )
