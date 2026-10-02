"""Public contracts and services for attachment metadata."""

from redmine_mcp.features.attachments.models import AttachmentDetail, AttachmentDownload
from redmine_mcp.features.attachments.ports import AttachmentReader
from redmine_mcp.features.attachments.service import AttachmentService

__all__ = ["AttachmentDetail", "AttachmentDownload", "AttachmentReader", "AttachmentService"]
