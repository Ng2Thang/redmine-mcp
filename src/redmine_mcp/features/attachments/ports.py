from typing import Protocol

from redmine_mcp.features.attachments.models import (
    AttachmentContainerRequest,
    AttachmentDeleteResult,
    AttachmentDetail,
    AttachmentDownload,
    AttachmentUpdateRequest,
    AttachmentUpdateResult,
    UploadResult,
)


class AttachmentReader(Protocol):
    async def get_attachment(self, attachment_id: int) -> AttachmentDetail: ...

    async def download_attachment(self, attachment_id: int) -> AttachmentDownload: ...


class AttachmentWriter(Protocol):
    async def upload_attachment(self, filename: str, content: bytes) -> UploadResult: ...


class AttachmentMetadataWriter(Protocol):
    async def update_attachment(
        self, attachment_id: int, request: AttachmentUpdateRequest
    ) -> AttachmentUpdateResult: ...


class AttachmentDeleter(Protocol):
    async def delete_attachment(
        self, attachment_id: int, request: AttachmentContainerRequest
    ) -> AttachmentDeleteResult: ...
