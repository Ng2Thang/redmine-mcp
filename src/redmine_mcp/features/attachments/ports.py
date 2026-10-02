from typing import Protocol

from redmine_mcp.features.attachments.models import (
    AttachmentDetail,
    AttachmentDownload,
    UploadResult,
)


class AttachmentReader(Protocol):
    async def get_attachment(self, attachment_id: int) -> AttachmentDetail: ...

    async def download_attachment(self, attachment_id: int) -> AttachmentDownload: ...


class AttachmentWriter(Protocol):
    async def upload_attachment(self, filename: str, content: bytes) -> UploadResult: ...
