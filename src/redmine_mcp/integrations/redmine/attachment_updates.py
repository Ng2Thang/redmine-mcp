"""Prove container membership before updating attachment metadata."""

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.attachments.models import (
    AttachmentContainerRequest,
    AttachmentUpdateRequest,
    AttachmentUpdateResult,
)
from redmine_mcp.features.issues.models import Attachment
from redmine_mcp.features.projects.models import Reference
from redmine_mcp.integrations.redmine.attachments import RedmineAttachments
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item
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

    async def contains_attachment(
        self, attachment_id: int, request: AttachmentContainerRequest
    ) -> bool:
        if request.container_type == "issue":
            data = await self.client.get(
                f"issues/{request.container_id}.json", {"include": "attachments"}
            )
            issue = resource_object(data.get("issue"), request.container_id)
            attachments = [
                item(Attachment, value) for value in response_items(issue, "attachments")
            ]
            matches = any(attachment.id == attachment_id for attachment in attachments)
        else:
            project_id = request.container_id
            if request.container_type == "version":
                data = await self.client.get(f"versions/{request.container_id}.json", {})
                version = resource_object(data.get("version"), request.container_id)
                project = item(Reference, response_object(version.get("project")))
                project_id = project.id
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
        return matches

    async def require_container(
        self, attachment_id: int, request: AttachmentContainerRequest
    ) -> None:
        if not await self.contains_attachment(attachment_id, request):
            raise ApplicationError(
                codes_text.RESOURCE_NOT_FOUND,
                redmine_text.RESOURCE_UNAVAILABLE,
                http_status.HTTP_404_NOT_FOUND,
            )

    async def update_attachment(
        self, attachment_id: int, request: AttachmentUpdateRequest
    ) -> AttachmentUpdateResult:
        await self.require_container(attachment_id, request)
        changes = request.model_dump(include={"filename", "description"}, exclude_unset=True)
        receipt = await self.writer.write_json(
            "PATCH",
            f"attachments/{attachment_id}.json",
            {"attachment": changes},
            accepted_statuses=(http_status.HTTP_204_NO_CONTENT,),
        )
        result = AttachmentUpdateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_204_NO_CONTENT else None,
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
