from pydantic import BaseModel, Field

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
