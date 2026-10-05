"""Prove container membership before updating attachment metadata."""

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.attachments.models import AttachmentUpdateRequest, AttachmentUpdateResult
from redmine_mcp.integrations.redmine.attachments import RedmineAttachments
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.projects import RedmineProjects
from redmine_mcp.integrations.redmine.responses import (
    resource_object,
    response_items,
    response_object,
)
from redmine_mcp.integrations.redmine.write import RedmineWriter


class RedmineAttachmentUpdates:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def _require_container(
        self, attachment_id: int, request: AttachmentUpdateRequest
    ) -> None:
        if request.container_type == "issue":
            data = await self.client.get(
                f"issues/{request.container_id}.json", {"include": "attachments"}
            )
            issue = resource_object(data.get("issue"), request.container_id)
            attachments = response_items(issue, "attachments")
            matches = any(
                type(item.get("id")) is int and item["id"] == attachment_id for item in attachments
            )
        else:
            project_id = request.container_id
            if request.container_type == "version":
                data = await self.client.get(f"versions/{request.container_id}.json", {})
                version = resource_object(data.get("version"), request.container_id)
                project = response_object(version.get("project"))
                owning_project_id = project.get("id")
                if type(owning_project_id) is not int or owning_project_id < 1:
                    raise ApplicationError(
                        codes_text.UPSTREAM_RESPONSE, redmine_text.UNEXPECTED_DATA, 502
                    )
                project_id = owning_project_id
            files = await RedmineProjects(self.client).list_project_files(project_id)
            matches = any(
                file.id == attachment_id
                and (
                    file.version is None
                    if request.container_type == "project"
                    else file.version is not None and file.version.id == request.container_id
                )
                for file in files.items
            )
        if not matches:
            raise ApplicationError(
                codes_text.RESOURCE_NOT_FOUND, redmine_text.RESOURCE_UNAVAILABLE, 404
            )

    async def update_attachment(
        self, attachment_id: int, request: AttachmentUpdateRequest
    ) -> AttachmentUpdateResult:
        await self._require_container(attachment_id, request)
        changes = request.model_dump(include={"filename", "description"}, exclude_unset=True)
        receipt = await self.writer.write_json(
            "PATCH",
            f"attachments/{attachment_id}.json",
            {"attachment": changes},
            accepted_statuses=(204,),
        )
        result = AttachmentUpdateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == 204 else None,
            attachment_id=attachment_id,
        )
        try:
            observed = await RedmineAttachments(self.client).get_attachment(attachment_id)
        except ApplicationError:
            return result
        result.observed_attachment = observed
        if any(
            observation.path == f"/{key}"
            for key in changes
            for observation in observed.visibility.observations
        ):
            return result
        result.verification = (
            "matched"
            if all(getattr(observed, key) == value for key, value in changes.items())
            else "mismatch"
        )
        return result
