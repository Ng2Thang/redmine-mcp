from typing import Protocol

from redmine_mcp.features.attachments.models import AttachmentDetail


class AttachmentReader(Protocol):
    async def get_attachment(self, attachment_id: int) -> AttachmentDetail: ...
