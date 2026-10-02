from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from redmine_mcp.common import Visibility
from redmine_mcp.features.projects import Reference


class AttachmentDetail(BaseModel):
    id: int = Field(gt=0)
    filename: str = Field(min_length=1)
    filesize: int = Field(ge=0)
    content_type: str | None = None
    description: str | None = None
    content_url: str = Field(min_length=1)
    author: Reference | None = None
    created_on: str = Field(min_length=1)
    visibility: Visibility = Field(default_factory=Visibility)


class AttachmentDownload(BaseModel):
    attachment_id: int = Field(gt=0)
    filename: str = Field(min_length=1)
    content_type: str | None = None
    content_base64: str
    filesize: int = Field(ge=0)
    visibility: Visibility = Field(default_factory=Visibility)


class UploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)


class UploadResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: bool | None
    verification: Literal["matched", "mismatch", "unavailable"] = "unavailable"
    attachment_id: int | None = Field(default=None, gt=0)
    token: str | None = None
    observed_filename: str | None = None
    observed_filesize: int | None = Field(default=None, ge=0)
