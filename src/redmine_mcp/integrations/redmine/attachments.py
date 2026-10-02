from base64 import b64encode

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError, Visibility
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
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
        metadata = await self.get_attachment(attachment_id)
        if metadata.filesize > self.client.policy.max_binary_bytes:
            raise ApplicationError(
                codes_text.UPSTREAM_RESPONSE_TOO_LARGE,
                redmine_text.RESPONSE_TOO_LARGE,
                http_status.HTTP_502_BAD_GATEWAY,
            )
        content = await self.client.get_attachment_bytes(metadata.content_url, attachment_id)
        if len(content) != metadata.filesize:
            raise ApplicationError(
                codes_text.UPSTREAM_RESPONSE,
                redmine_text.UNEXPECTED_DATA,
                http_status.HTTP_502_BAD_GATEWAY,
            )
        return AttachmentDownload(
            attachment_id=attachment_id,
            filename=metadata.filename,
            content_type=metadata.content_type,
            content_base64=b64encode(content).decode("ascii"),
            filesize=len(content),
            visibility=Visibility(
                observations=[
                    observation
                    for observation in metadata.visibility.observations
                    if observation.path == "/content_type"
                ]
            ),
        )
