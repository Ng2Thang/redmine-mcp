"""Validated inputs and receipts for issue creation and native copying."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from redmine_mcp.common import PositiveID, Visibility
from redmine_mcp.features.issues.models import IssueDate, IssueDetail, IssueHours, Journal

PositiveIssueId = PositiveID
Verification = Literal["matched", "mismatch", "unavailable"]


class IssueCustomFieldInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: PositiveIssueId
    value: str | list[str] | None


class IssueUploadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=3, max_length=200, repr=False)
    filename: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    content_type: str | None = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_upload(self) -> "IssueUploadInput":
        if not re.fullmatch(r"[1-9][0-9]*\.[0-9a-f]+", self.token):
            raise ValueError("Invalid upload token")
        if (
            self.filename in (".", "..")
            or any(character in self.filename for character in ("/", "\\"))
            or any(ord(character) < 32 or ord(character) == 127 for character in self.filename)
        ):
            raise ValueError("Invalid attachment filename")
        if any(
            getattr(self, field) is None
            for field in self.model_fields_set.intersection({"description", "content_type"})
        ):
            raise ValueError("Upload metadata must be strings when supplied")
        return self


class IssueCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: PositiveIssueId
    copy_from: PositiveIssueId | None = None
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    tracker_id: PositiveIssueId | None = None
    status_id: PositiveIssueId | None = None
    priority_id: PositiveIssueId | None = None
    category_id: PositiveIssueId | None = None
    fixed_version_id: PositiveIssueId | None = None
    assigned_to_id: PositiveIssueId | Literal["me"] | None = None
    parent_issue_id: PositiveIssueId | None = None
    description: str | None = None
    start_date: IssueDate | None = None
    due_date: IssueDate | None = None
    done_ratio: int | None = Field(default=None, strict=True, ge=0, le=100)
    estimated_hours: IssueHours | None = None
    is_private: bool | None = Field(default=None, strict=True)
    custom_fields: list[IssueCustomFieldInput] | None = None
    uploads: list[IssueUploadInput] | None = Field(default=None, repr=False)
    watcher_user_ids: list[PositiveIssueId] | None = None

    @model_validator(mode="after")
    def validate_creation(self) -> "IssueCreateRequest":
        nonnullable = {
            "copy_from",
            "subject",
            "tracker_id",
            "status_id",
            "priority_id",
            "done_ratio",
            "is_private",
            "custom_fields",
            "uploads",
            "watcher_user_ids",
        }
        if any(getattr(self, field) is None for field in self.model_fields_set & nonnullable):
            raise ValueError("A supplied creation field must not be null")
        if self.copy_from is None and self.subject is None:
            raise ValueError("Subject is required without copy_from")
        if self.subject is not None and not self.subject.strip():
            raise ValueError("Subject must not be blank")
        if self.start_date is not None and self.due_date is not None:
            if self.due_date < self.start_date:
                raise ValueError("Due date must not precede start date")
        custom_ids = [field.id for field in self.custom_fields or []]
        upload_ids = [upload.token.split(".", 1)[0] for upload in self.uploads or []]
        for values in (custom_ids, upload_ids, self.watcher_user_ids or []):
            if len(values) != len(set(values)):
                raise ValueError("Duplicate custom fields, uploads, or watchers are not accepted")
        return self


class IssueCreateResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    resource_id: PositiveID | None = None
    verification: Verification = "unavailable"
    field_verification: dict[str, Verification] = Field(default_factory=dict)
    observed_issue: IssueDetail | None = None


class IssueUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: PositiveIssueId | None = None
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    tracker_id: PositiveIssueId | None = None
    status_id: PositiveIssueId | None = None
    priority_id: PositiveIssueId | None = None
    category_id: PositiveIssueId | None = None
    fixed_version_id: PositiveIssueId | None = None
    assigned_to_id: PositiveIssueId | Literal["me"] | None = None
    parent_issue_id: PositiveIssueId | None = None
    description: str | None = None
    start_date: IssueDate | None = None
    due_date: IssueDate | None = None
    done_ratio: int | None = Field(default=None, strict=True, ge=0, le=100)
    estimated_hours: IssueHours | None = None
    is_private: bool | None = Field(default=None, strict=True)
    custom_fields: list[IssueCustomFieldInput] | None = None
    uploads: list[IssueUploadInput] | None = Field(default=None, repr=False)
    notes: str | None = Field(default=None, min_length=1, repr=False)
    private_notes: bool | None = Field(default=None, strict=True)

    @model_validator(mode="after")
    def validate_update(self) -> "IssueUpdateRequest":
        nonnullable = {
            "project_id",
            "subject",
            "tracker_id",
            "status_id",
            "priority_id",
            "done_ratio",
            "is_private",
            "custom_fields",
            "uploads",
            "notes",
            "private_notes",
        }
        if any(getattr(self, field) is None for field in self.model_fields_set & nonnullable):
            raise ValueError("A supplied non-clearable update field must not be null")
        effective_fields = self.model_fields_set.difference({"private_notes"})
        if not self.custom_fields:
            effective_fields.discard("custom_fields")
        if not self.uploads:
            effective_fields.discard("uploads")
        if not effective_fields:
            raise ValueError("Supply at least one issue field, upload, custom field, or note")
        if self.private_notes is not None and self.notes is None:
            raise ValueError("private_notes requires notes")
        if any(value is not None and not value.strip() for value in (self.subject, self.notes)):
            raise ValueError("Subject and notes must not be blank")
        if self.start_date is not None and self.due_date is not None:
            if self.due_date < self.start_date:
                raise ValueError("Due date must not precede start date")
        custom_ids = [field.id for field in self.custom_fields or []]
        upload_ids = [upload.token.split(".", 1)[0] for upload in self.uploads or []]
        for values in (custom_ids, upload_ids):
            if len(values) != len(set(values)):
                raise ValueError("Duplicate custom fields or uploads are not accepted")
        return self


class IssueUpdateResult(IssueCreateResult):
    resource_id: PositiveIssueId
    journal_id: PositiveIssueId | None = None


class IssueNoteUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(default=None, repr=False)
    private_notes: bool | None = Field(default=None, strict=True)

    @model_validator(mode="after")
    def validate_note_update(self) -> "IssueNoteUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("Supply notes or private_notes")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Supplied note fields must not be null")
        return self


class JournalObservation(Journal):
    visibility: Visibility = Field(default_factory=Visibility)


class IssueNoteUpdateResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    issue_id: PositiveIssueId
    resource_id: PositiveIssueId
    verification: Verification = "unavailable"
    field_verification: dict[str, Verification] = Field(default_factory=dict)
    observed_present: StrictBool | None = None
    observed_journal: JournalObservation | None = None


RelationType = Literal[
    "relates",
    "duplicates",
    "duplicated",
    "blocks",
    "blocked",
    "precedes",
    "follows",
    "copied_to",
    "copied_from",
]


class IssueRelationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_to_id: PositiveIssueId
    relation_type: RelationType = "relates"
    delay: int | None = Field(default=None, strict=True)

    @model_validator(mode="after")
    def validate_delay(self) -> "IssueRelationCreateRequest":
        if "delay" in self.model_fields_set:
            if self.delay is None or self.relation_type not in ("precedes", "follows"):
                raise ValueError("Delay must be an integer and requires precedes or follows")
        return self


class RelationObservation(BaseModel):
    id: PositiveIssueId
    issue_id: PositiveIssueId
    issue_to_id: PositiveIssueId
    relation_type: RelationType
    delay: int | None = Field(default=None, strict=True)
    visibility: Visibility = Field(default_factory=Visibility)


class IssueRelationCreateResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    resource_id: PositiveIssueId | None = None
    verification: Verification = "unavailable"
    field_verification: dict[str, Verification] = Field(default_factory=dict)
    observed_relation: RelationObservation | None = None


class IssueRelationDeleteResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    resource_id: PositiveIssueId
    resolved_relation: RelationObservation
    endpoint_observations: dict[str, StrictBool | None] = Field(default_factory=dict)
    observed_present: StrictBool | None = None
    verification: Verification = "unavailable"


class IssueWatcherAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: PositiveIssueId


class IssueWatcherResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    issue_id: PositiveIssueId
    user_id: PositiveIssueId
    observed_present: StrictBool | None = None
    verification: Verification = "unavailable"
