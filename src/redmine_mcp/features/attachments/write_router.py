from typing import Annotated

from fastapi import APIRouter, Depends, Path

from redmine_mcp.api import get_attachments, require_write_access
from redmine_mcp.features.attachments.models import (
    AttachmentUpdateRequest,
    AttachmentUpdateResult,
    UploadRequest,
    UploadResult,
)
from redmine_mcp.features.attachments.service import AttachmentService

router = APIRouter(
    prefix="/api/v1/uploads", tags=["attachments"], dependencies=[Depends(require_write_access)]
)
metadata_router = APIRouter(
    prefix="/api/v1/attachments",
    tags=["attachments"],
    dependencies=[Depends(require_write_access)],
)


@router.post(
    "",
    operation_id="upload_attachment",
    response_model=UploadResult,
    description=(
        "Upload a bounded base64 attachment to Redmine as a temporary unattached object. "
        "The writer deployment must allow this operation. Return its opaque token and ID "
        "when Redmine confirms them; an uncertain result must be reconciled before retrying."
    ),
)
async def upload_attachment(
    request: UploadRequest,
    service: Annotated[AttachmentService, Depends(get_attachments)],
) -> UploadResult:
    return await service.upload_attachment(request.filename, request.content_base64)


@metadata_router.patch(
    "/{attachment_id}",
    operation_id="update_attachment",
    response_model=AttachmentUpdateResult,
    description=(
        "Update an attachment's supplied filename or description after confirming it belongs "
        "to the declared project, version, or issue. Empty description clears it; omitted "
        "fields are preserved. Reports write acceptance separately from metadata read-back. "
        "This operation requires the restricted writer deployment and container edit permission."
    ),
)
async def update_attachment(
    request: AttachmentUpdateRequest,
    service: Annotated[AttachmentService, Depends(get_attachments)],
    attachment_id: Annotated[int, Path(ge=1, description="ID of the attachment")],
) -> AttachmentUpdateResult:
    return await service.update_attachment(attachment_id, request)
