from typing import Annotated

from pydantic import BaseModel, Field, JsonValue, WithJsonSchema

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


class IssueChild(BaseModel):
    id: int = Field(gt=0)
    tracker: Reference | None = None
    subject: str
    # FastAPI-MCP 0.4 cannot expand recursive OpenAPI references.
    children: Annotated[
        list["IssueChild"],
        WithJsonSchema(
            {
                "type": "array",
                "description": "Child issues may contain further nested children.",
                "items": {
                    "type": "object",
                    "required": ["id", "subject"],
                    "properties": {
                        "id": {"type": "integer"},
                        "tracker": {
                            "anyOf": [
                                {"$ref": "#/components/schemas/Reference"},
                                {"type": "null"},
                            ]
                        },
                        "subject": {"type": "string"},
                        "children": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Nested issue children have the same fields.",
                        },
                    },
                },
            }
        ),
    ] = Field(default_factory=list)


class IssueRelation(BaseModel):
    id: int = Field(gt=0)
    issue_id: int = Field(gt=0)
    issue_to_id: int = Field(gt=0)
    relation_type: str
    delay: int | None = None


class AllowedStatus(BaseModel):
    id: int = Field(gt=0)
    name: str
    is_closed: bool


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
    category: Reference | None = None
    parent: dict[str, int] | None = None
    is_private: bool = False
    done_ratio: int = 0
    created_on: str
    updated_on: str
    custom_fields: list[CustomField] = Field(default_factory=list)
    journals: list[Journal] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    children: list[IssueChild] = Field(default_factory=list)
    relations: list[IssueRelation] = Field(default_factory=list)
    # JsonValue also uses a recursive OpenAPI reference; keep runtime validation.
    changesets: Annotated[
        list[dict[str, JsonValue]],
        WithJsonSchema({"type": "array", "items": {"type": "object"}}),
    ] = Field(default_factory=list)
    watchers: list[Reference] = Field(default_factory=list)
    allowed_statuses: list[AllowedStatus] = Field(default_factory=list)
