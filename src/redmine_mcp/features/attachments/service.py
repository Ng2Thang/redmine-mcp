from redmine_mcp.common import require_positive_id
from redmine_mcp.features.attachments.models import AttachmentDetail
from redmine_mcp.features.attachments.ports import AttachmentReader


class AttachmentService:
    def __init__(self, reader: AttachmentReader) -> None:
        self.reader = reader

    async def get_attachment(self, attachment_id: int) -> AttachmentDetail:
        require_positive_id(attachment_id, "attachment_id")
        return await self.reader.get_attachment(attachment_id)
