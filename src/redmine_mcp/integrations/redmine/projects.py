from fastapi import status as http_status

from redmine_mcp.common import ApplicationError, Collection, FieldObservation, Page, Visibility
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.projects import (
    IssueCategory,
    Project,
    ProjectDetail,
    ProjectFile,
    ProjectTimeEntryActivity,
    Version,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import page, visible_item, wrapped_collection
from redmine_mcp.integrations.redmine.responses import resource_object


class RedmineProjects:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def list_projects(self, limit: int, offset: int) -> Page[Project]:
        data = await self.client.get_page(
            "projects.json",
            "projects",
            {"limit": limit, "offset": offset},
            "Use get_project with a known project ID; this project list requires too many pages",
        )
        result = page(Project, data, "projects", limit, offset)
        result.pagination_policy = self.client.pagination.describe(result.total, limit)
        return result

    async def get_project(self, project_id: int) -> ProjectDetail:
        data = await self.client.get(f"projects/{project_id}.json", {})
        return visible_item(ProjectDetail, resource_object(data.get("project"), project_id))

    async def list_project_versions(self, project_id: int) -> Collection[Version]:
        data = await self.client.get(f"projects/{project_id}/versions.json", {})
        return wrapped_collection(Version, data, "versions", complete=True)

    async def list_project_issue_categories(self, project_id: int) -> Collection[IssueCategory]:
        data = await self.client.get(f"projects/{project_id}/issue_categories.json", {})
        return wrapped_collection(IssueCategory, data, "issue_categories", complete=True)

    async def list_project_files(self, project_id: int) -> Collection[ProjectFile]:
        data = await self.client.get(f"projects/{project_id}/files.json", {})
        return wrapped_collection(ProjectFile, data, "files")

    async def list_project_time_entry_activities(
        self, project_id: int
    ) -> Collection[ProjectTimeEntryActivity]:
        data = await self.client.get(
            f"projects/{project_id}.json", {"include": "time_entry_activities"}
        )
        project = resource_object(data.get("project"), project_id)
        if "time_entry_activities" not in project:
            return Collection(
                items=[],
                visibility=Visibility(
                    observations=[FieldObservation(path="/items", state="not_returned")]
                ),
            )
        result = wrapped_collection(ProjectTimeEntryActivity, project, "time_entry_activities")
        if len({activity.id for activity in result.items}) != len(result.items):
            raise ApplicationError(
                codes_text.UPSTREAM_RESPONSE,
                redmine_text.UNEXPECTED_DATA,
                http_status.HTTP_502_BAD_GATEWAY,
            )
        return result
