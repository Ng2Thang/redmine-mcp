"""Delete an attachment only after proving its declared container membership."""

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.attachments.models import (
    AttachmentContainerRequest,
    AttachmentDeleteResult,
)
from redmine_mcp.integrations.redmine.attachment_updates import RedmineAttachmentUpdates
from redmine_mcp.integrations.redmine.write import RedmineWriter


class RedmineAttachmentDeletions:
    def __init__(self, writer: RedmineWriter, containers: RedmineAttachmentUpdates) -> None:
        self.writer = writer
        self.containers = containers

    async def delete_attachment(
        self, attachment_id: int, request: AttachmentContainerRequest
    ) -> AttachmentDeleteResult:
        await self.containers.require_container(attachment_id, request)
        receipt = await self.writer.write_json(
            "DELETE", f"attachments/{attachment_id}.json", accepted_statuses=(204,)
        )
        result = AttachmentDeleteResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == 204 else None,
            attachment_id=attachment_id,
        )
        try:
            present = await self.containers.contains_attachment(attachment_id, request)
        except ApplicationError:
            return result
        result.observed_present = present
        result.verification = "mismatch" if present else "matched"
        return result
