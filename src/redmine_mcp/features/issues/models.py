import re
from datetime import date
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    JsonValue,
    StrictBool,
    StrictInt,
    WithJsonSchema,
    field_validator,
)

from redmine_mcp.common import NonnegativeInt, PositiveID, Visibility
from redmine_mcp.constants import issues as issues_text
from redmine_mcp.features.projects import Reference

ISSUE_INCLUDES = frozenset(
    {
        "children",
        "attachments",
        "relations",
        "changesets",
        "journals",
        "watchers",
        "allowed_statuses",
    }
)
ISSUE_LIST_INCLUDES = frozenset({"attachments", "relations"})


def require_issue_date(value: object) -> object:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(issues_text.ISO_DATE_REQUIRED)
    return value


def require_hour_number(value: object) -> object:
    if type(value) not in (int, float):
        raise ValueError(issues_text.JSON_NUMBER_REQUIRED)
    return value


IssueDate = Annotated[date, BeforeValidator(require_issue_date)]
IssueHours = Annotated[
    float,
    BeforeValidator(require_hour_number),
    Field(ge=0, allow_inf_nan=False),
]


class CustomField(BaseModel):
    id: PositiveID
    name: str
    value: str | list[str] | None = None
    multiple: StrictBool = False


class JournalDetail(BaseModel):
    property: str
    name: str
    old_value: str | None = None
    new_value: str | None = None


class Journal(BaseModel):
    id: PositiveID
    user: Reference
    notes: str = ""
    created_on: str
    updated_on: str | None = None
    updated_by: Reference | None = None
    private_notes: StrictBool = False
    details: list[JournalDetail] = Field(default_factory=list)


class Attachment(BaseModel):
    id: PositiveID
    filename: str
    filesize: NonnegativeInt
    content_type: str | None = None
    description: str | None = None
    content_url: str | None = None
    created_on: str
    author: Reference


class IssueChild(BaseModel):
    id: PositiveID
    tracker: Reference | None = None
    subject: str
    # FastAPI-MCP 0.4 cannot expand recursive OpenAPI references.
    children: Annotated[
        list["IssueChild"],
        WithJsonSchema(
            {
                "type": "array",
                "description": ("Child issues may contain further nested children."),
                "items": {
                    "type": "object",
                    "required": ["id", "subject"],
                    "properties": {
                        "id": {"type": "integer", "exclusiveMinimum": 0},
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
                            "description": ("Nested issue children have the same fields."),
                        },
                    },
                },
            }
        ),
    ] = Field(default_factory=list)


class IssueRelation(BaseModel):
    id: PositiveID
    issue_id: PositiveID
    issue_to_id: PositiveID
    relation_type: str
    delay: StrictInt | None = None


class AllowedStatus(BaseModel):
    id: PositiveID
    name: str
    is_closed: StrictBool


class Issue(BaseModel):
    id: PositiveID
    subject: str
    description: str | None = None
    project: Reference
    tracker: Reference
    status: Reference
    priority: Reference
    author: Reference
    assigned_to: Reference | None = None
    category: Reference | None = None
    fixed_version: Reference | None = None
    parent: dict[str, int] | None = None
    is_private: StrictBool = False
    done_ratio: int = Field(default=0, strict=True, ge=0, le=100)
    start_date: IssueDate | None = None
    due_date: IssueDate | None = None
    spent_hours: IssueHours | None = None
    total_spent_hours: IssueHours | None = None
    estimated_hours: IssueHours | None = None
    total_estimated_hours: IssueHours | None = None
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

    @field_validator("parent", mode="before")
    @classmethod
    def validate_parent_id(cls, value: object) -> object:
        if value is not None:
            if not isinstance(value, dict) or type(value.get("id")) is not int or value["id"] < 1:
                raise ValueError("Parent must identify a positive integer issue ID")
        return value


class IssueDetail(Issue):
    visibility: Visibility = Field(default_factory=Visibility)
