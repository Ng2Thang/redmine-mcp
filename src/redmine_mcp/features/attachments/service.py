from base64 import b64decode
from binascii import Error as Base64Error
from http import HTTPStatus

from redmine_mcp.auth.capability_models import WriteIntent
from redmine_mcp.auth.capability_ports import WriteAuthorizer
from redmine_mcp.common import ApplicationError, require_positive_id
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.attachments.models import (
    AttachmentContainerRequest,
    AttachmentDeleteResult,
    AttachmentDetail,
    AttachmentDownload,
    AttachmentUpdateRequest,
    AttachmentUpdateResult,
    UploadResult,
)
from redmine_mcp.features.attachments.ports import (
    AttachmentDeleter,
    AttachmentMetadataWriter,
    AttachmentReader,
    AttachmentWriter,
)


class AttachmentService:
    def __init__(
        self,
        reader: AttachmentReader,
        writer: AttachmentWriter | None = None,
        max_binary_bytes: int = 5 * 1024 * 1024,
        metadata_writer: AttachmentMetadataWriter | None = None,
        deleter: AttachmentDeleter | None = None,
        authorizer: WriteAuthorizer | None = None,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.max_binary_bytes = max_binary_bytes
        self.metadata_writer = metadata_writer
        self.deleter = deleter
        self.authorizer = authorizer

    async def get_attachment(self, attachment_id: int) -> AttachmentDetail:
        require_positive_id(attachment_id, "attachment_id")
        return await self.reader.get_attachment(attachment_id)

    async def download_attachment(self, attachment_id: int) -> AttachmentDownload:
        require_positive_id(attachment_id, "attachment_id")
        return await self.reader.download_attachment(attachment_id)

    async def update_attachment(
        self, attachment_id: int, request: AttachmentUpdateRequest
    ) -> AttachmentUpdateResult:
        require_positive_id(attachment_id, "attachment_id")
        if self.metadata_writer is None:
            raise RuntimeError("Attachment metadata writer is not configured")
        if self.authorizer is not None:
            await self.authorizer.authorize(
                WriteIntent(
                    "update_attachment",
                    attachment_id=attachment_id,
                    container_type=request.container_type,
                    container_id=request.container_id,
                )
            )
        return await self.metadata_writer.update_attachment(attachment_id, request)

    async def delete_attachment(
        self, attachment_id: int, request: AttachmentContainerRequest
    ) -> AttachmentDeleteResult:
        require_positive_id(attachment_id, "attachment_id")
        require_positive_id(request.container_id, "container_id")
        if self.deleter is None:
            raise RuntimeError("Attachment deleter is not configured")
        if self.authorizer is not None:
            await self.authorizer.authorize(
                WriteIntent(
                    "delete_attachment",
                    attachment_id=attachment_id,
                    container_type=request.container_type,
                    container_id=request.container_id,
                )
            )
        return await self.deleter.delete_attachment(attachment_id, request)

    async def upload_attachment(self, filename: str, content_base64: str) -> UploadResult:
        if (
            not filename
            or len(filename) > 255
            or filename in (".", "..")
            or any(character in filename for character in ("/", "\\", "\x00"))
            or any(ord(character) < 32 or ord(character) == 127 for character in filename)
        ):
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.INVALID_FILENAME,
                HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        maximum_encoded = 4 * ((self.max_binary_bytes + 2) // 3)
        if len(content_base64) > maximum_encoded:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.REQUEST_TOO_LARGE,
                HTTPStatus.CONTENT_TOO_LARGE,
            )
        try:
            content = b64decode(content_base64, validate=True)
        except (Base64Error, ValueError):
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.INVALID_BASE64,
                HTTPStatus.UNPROCESSABLE_ENTITY,
            ) from None
        if len(content) > self.max_binary_bytes:
            raise ApplicationError(
                codes_text.INVALID_PARAMETERS,
                redmine_text.REQUEST_TOO_LARGE,
                HTTPStatus.CONTENT_TOO_LARGE,
            )
        if self.writer is None:
            raise RuntimeError("Attachment writer is not configured")
        if self.authorizer is not None:
            await self.authorizer.authorize(WriteIntent("upload_attachment"))
        return await self.writer.upload_attachment(filename, content)
