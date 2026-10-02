from typing import Annotated

from fastapi import APIRouter, Depends

from redmine_mcp.api import get_attachments, require_write_access
from redmine_mcp.features.attachments.models import UploadRequest, UploadResult
from redmine_mcp.features.attachments.service import AttachmentService

router = APIRouter(
    prefix="/api/v1/uploads", tags=["attachments"], dependencies=[Depends(require_write_access)]
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
