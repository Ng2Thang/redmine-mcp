"""Validated time-entry write inputs and independent observation receipts."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from redmine_mcp.common import PositiveID
from redmine_mcp.features.issues import IssueDate, IssueHours
from redmine_mcp.features.time_entries.models import TimeEntry

TimeEntryVerification = Literal["matched", "mismatch", "unavailable"]


class TimeEntryCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hours: Annotated[IssueHours, Field(gt=0)]
    spent_on: IssueDate
    activity_id: PositiveID | None = None
    comments: str | None = Field(default=None, strict=True, max_length=1024)

    @model_validator(mode="after")
    def require_supplied_values(self) -> "TimeEntryCreateRequest":
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Supplied time-entry fields must not be null")
        return self


class TimeEntryCreateResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    resource_id: PositiveID | None = None
    verification: TimeEntryVerification = "unavailable"
    field_verification: dict[str, TimeEntryVerification] = Field(default_factory=dict)
    observed_time_entry: TimeEntry | None = None


class TimeEntryUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hours: Annotated[IssueHours, Field(gt=0)] | None = None
    spent_on: IssueDate | None = None
    activity_id: PositiveID | None = None
    comments: str | None = Field(default=None, strict=True, max_length=1024)

    @model_validator(mode="after")
    def require_supplied_values(self) -> "TimeEntryUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("Supply at least one time-entry field")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Supplied time-entry fields must not be null")
        return self


class TimeEntryUpdateResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    resource_id: PositiveID
    issue_id: PositiveID
    verification: TimeEntryVerification = "unavailable"
    field_verification: dict[str, TimeEntryVerification] = Field(default_factory=dict)
    observed_time_entry: TimeEntry | None = None


class TimeEntryDeleteResult(BaseModel):
    outcome: Literal["accepted", "uncertain"]
    upstream_accepted: StrictBool | None
    resource_id: PositiveID
    issue_id: PositiveID
    verification: Literal["not_found", "still_present", "unavailable"] = "unavailable"
    observed_present: StrictBool | None = None
