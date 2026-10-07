from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from redmine_mcp.common import NonnegativeInt, PositiveID, Visibility
from redmine_mcp.features.projects import Reference


class AttachmentDetail(BaseModel):
    id: PositiveID
    filename: str = Field(min_length=1)
    filesize: NonnegativeInt
    content_type: str | None = None
    description: str | None = None
    content_url: str = Field(min_length=1)
    author: Reference | None = None
    created_on: str = Field(min_length=1)
    visibility: Visibility = Field(default_factory=Visibility)


class AttachmentDownload(BaseModel):
    attachment_id: PositiveID
    filename: str = Field(min_length=1)
    content_type: str | None = None
    content_base64: str
    filesize: NonnegativeInt
    visibility: Visibility = Field(default_factory=Visibility)


class UploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)


class UploadResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    verification: Literal["matched", "mismatch", "unavailable"] = "unavailable"
    attachment_id: PositiveID | None = None
    token: str | None = None
    observed_filename: str | None = None
    observed_filesize: NonnegativeInt | None = None


class AttachmentContainerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    container_type: Literal["project", "version", "issue"]
    container_id: int = Field(strict=True, gt=0)


class AttachmentDeleteQuery(AttachmentContainerRequest):
    # Query values arrive as strings; the resulting service ID remains an integer.
    container_id: int = Field(gt=0)


class AttachmentUpdateRequest(AttachmentContainerRequest):
    filename: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_changes(self) -> "AttachmentUpdateRequest":
        supplied = self.model_fields_set.intersection({"filename", "description"})
        if not supplied or any(getattr(self, field) is None for field in supplied):
            raise ValueError("Supply filename or description as a string; null is not accepted")
        if self.filename is not None and (
            self.filename in (".", "..")
            or any(character in self.filename for character in ("/", "\\"))
            or any(ord(character) < 32 or ord(character) == 127 for character in self.filename)
        ):
            raise ValueError("Invalid attachment filename")
        return self


class AttachmentUpdateResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    verification: Literal["matched", "mismatch", "unavailable"] = "unavailable"
    attachment_id: PositiveID
    observed_attachment: AttachmentDetail | None = None


class AttachmentDeleteResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    verification: Literal["matched", "mismatch", "unavailable"] = "unavailable"
    attachment_id: PositiveID
    observed_present: StrictBool | None = None
