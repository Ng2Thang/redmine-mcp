"""Map Redmine's temporary upload response to a caller-visible receipt."""

import re

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.attachments.models import UploadResult
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.write import RedmineWriter


class RedmineUploads:
    def __init__(self, writer: RedmineWriter, reader: RedmineClient) -> None:
        self.writer = writer
        self.reader = reader

    async def upload_attachment(self, filename: str, content: bytes) -> UploadResult:
        receipt = await self.writer.write_binary("uploads.json", content, filename=filename)
        if receipt.outcome == "uncertain":
            return UploadResult(
                outcome="uncertain",
                upstream_accepted=True if receipt.status == 201 else None,
            )
        upload = receipt.payload.get("upload") if receipt.payload is not None else None
        if not isinstance(upload, dict):
            return UploadResult(outcome="uncertain", upstream_accepted=True)
        attachment_id = upload.get("id")
        token = upload.get("token")
        if (
            type(attachment_id) is not int
            or attachment_id < 1
            or not isinstance(token, str)
            or not re.fullmatch(rf"{attachment_id}\.[0-9a-f]+", token)
        ):
            return UploadResult(outcome="uncertain", upstream_accepted=True)
        result = UploadResult(
            outcome="accepted", upstream_accepted=True, attachment_id=attachment_id, token=token
        )
        try:
            data = await self.reader.get(f"attachments/{attachment_id}.json", {})
        except ApplicationError:
            return result
        observed = data.get("attachment")
        if not isinstance(observed, dict):
            return result
        observed_id = observed.get("id")
        observed_filename = observed.get("filename")
        observed_filesize = observed.get("filesize")
        if (
            type(observed_id) is not int
            or type(observed_filename) is not str
            or type(observed_filesize) is not int
            or observed_filesize < 0
        ):
            return result
        result.observed_filename = observed_filename
        result.observed_filesize = observed_filesize
        result.verification = (
            "matched"
            if observed_id == attachment_id
            and observed_filename == filename
            and observed_filesize == len(content)
            else "mismatch"
        )
        return result
