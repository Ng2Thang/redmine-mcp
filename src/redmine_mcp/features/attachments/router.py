from typing import Annotated

from fastapi import APIRouter, Depends, Path

from redmine_mcp.api import get_attachments, require_read_access
from redmine_mcp.common import ApplicationError
from redmine_mcp.features.attachments.models import AttachmentDetail, AttachmentDownload
from redmine_mcp.features.attachments.service import AttachmentService

router = APIRouter(
    prefix="/api/v1/attachments", tags=["attachments"], dependencies=[Depends(require_read_access)]
)


@router.get(
    "/{attachment_id}",
    operation_id="get_attachment",
    response_model=AttachmentDetail,
    description=(
        "Read metadata for one attachment visible to the requesting Redmine user. "
        "Returns its filename, size, content type, description, content URL, author, "
        "and creation time with visibility metadata. Redmine checks access to the "
        "attachment's container. This operation does not download the file."
    ),
)
async def get_attachment(
    service: Annotated[AttachmentService, Depends(get_attachments)],
    attachment_id: Annotated[int, Path(ge=1, description="ID of the attachment")],
) -> AttachmentDetail:
    """Read attachment metadata without downloading its content."""
    return await service.get_attachment(attachment_id)


@router.get(
    "/{attachment_id}/content",
    operation_id="download_attachment",
    include_in_schema=False,
    response_model=AttachmentDownload,
    description="Disabled: use get_attachment for a Redmine browser download link.",
)
async def download_attachment(
    service: Annotated[AttachmentService, Depends(get_attachments)],
    attachment_id: Annotated[int, Path(ge=1, description="ID of the attachment")],
) -> AttachmentDownload:
    """Retired content route, also rejected by middleware before authentication."""
    raise ApplicationError(
        "attachment_download_disabled", "Use attachment metadata and its Redmine link", 403
    )
