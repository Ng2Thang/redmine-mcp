from redmine_mcp.common import ApplicationError
from redmine_mcp.features.attachments import AttachmentDetail, AttachmentDownload
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import visible_item
from redmine_mcp.integrations.redmine.responses import resource_object


class RedmineAttachments:
    def __init__(self, client: RedmineClient) -> None:
        self.client = client

    async def get_attachment(self, attachment_id: int) -> AttachmentDetail:
        data = await self.client.get(f"attachments/{attachment_id}.json", {})
        return visible_item(
            AttachmentDetail,
            resource_object(data.get("attachment"), attachment_id),
            observed_fields=("content_type", "description", "author"),
        )

    async def download_attachment(self, attachment_id: int) -> AttachmentDownload:
        raise ApplicationError(
            "attachment_download_disabled", "Use attachment metadata and its Redmine link", 403
        )
