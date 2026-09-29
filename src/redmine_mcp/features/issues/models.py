from pydantic import BaseModel, Field

from redmine_mcp.features.projects.models import Reference


class CustomField(BaseModel):
    id: int
    name: str
    value: str | list[str] | None = None
    multiple: bool = False


class JournalDetail(BaseModel):
    property: str
    name: str
    old_value: str | None = None
    new_value: str | None = None


class Journal(BaseModel):
    id: int
    user: Reference
    notes: str = ""
    created_on: str
    private_notes: bool = False
    details: list[JournalDetail] = Field(default_factory=list)


class Attachment(BaseModel):
    id: int
    filename: str
    filesize: int
    content_type: str | None = None
    description: str | None = None
    created_on: str
    author: Reference


class Issue(BaseModel):
    id: int
    subject: str
    description: str | None = None
    project: Reference
    tracker: Reference
    status: Reference
    priority: Reference
    author: Reference
    assigned_to: Reference | None = None
    parent: dict[str, int] | None = None
    is_private: bool = False
    done_ratio: int = 0
    created_on: str
    updated_on: str
    custom_fields: list[CustomField] = Field(default_factory=list)
    journals: list[Journal] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
