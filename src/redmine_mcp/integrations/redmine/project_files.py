"""Attach one upload token to a project and inspect the resulting file."""

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.projects.models import AddProjectFileResult
from redmine_mcp.integrations.redmine.projects import RedmineProjects
from redmine_mcp.integrations.redmine.write import RedmineWriter


class RedmineProjectFiles:
    def __init__(self, writer: RedmineWriter, reader: RedmineProjects) -> None:
        self.writer = writer
        self.reader = reader

    async def add_project_file(
        self,
        project_id: int,
        token: str,
        filename: str,
        description: str | None,
        version_id: int | None,
        attachment_id: int,
    ) -> AddProjectFileResult:
        file: dict[str, str | int] = {"token": token, "filename": filename}
        if description is not None:
            file["description"] = description
        if version_id is not None:
            file["version_id"] = version_id
        receipt = await self.writer.write_json(
            "POST",
            f"projects/{project_id}/files.json",
            {"file": file},
            accepted_statuses=(http_status.HTTP_204_NO_CONTENT,),
        )
        result = AddProjectFileResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_204_NO_CONTENT else None,
            attachment_id=attachment_id,
        )
        try:
            files = await self.reader.list_project_files(project_id)
        except ApplicationError:
            return result
        observed = next((item for item in files.items if item.id == attachment_id), None)
        if observed is None:
            result.verification = "mismatch"
            return result
        result.observed_file = observed
        result.verification = (
            "matched"
            if observed.filename == filename
            and (observed.version.id if observed.version is not None else None) == version_id
            and (description is None or observed.description == description)
            else "mismatch"
        )
        return result
