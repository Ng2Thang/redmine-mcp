"""Create one caller-credited entry with a single POST and independent verification."""

from decimal import ROUND_HALF_UP, Decimal, localcontext
from http import HTTPMethod
from typing import Any

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.time_entries.models import TimeEntryIssueReference
from redmine_mcp.features.time_entries.write_models import (
    TimeEntryCreateRequest,
    TimeEntryCreateResult,
    TimeEntryVerification,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item
from redmine_mcp.integrations.redmine.responses import resource_object
from redmine_mcp.integrations.redmine.time_entries import map_time_entry
from redmine_mcp.integrations.redmine.write import RedmineWriter

REFERENCE_FIELDS = {
    "issue_id": "issue",
    "project_id": "project",
    "user_id": "user",
    "activity_id": "activity",
}


def normalized_hours(value: float) -> Decimal:
    """Match pinned Redmine's whole-minute getter and two-decimal API output."""
    number = Decimal(str(value))
    with localcontext() as context:
        context.prec = max(32, number.adjusted() + 8)
        minutes = (number * 60).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return (minutes / 60).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def verify_fields(
    actual: dict[str, Any], expected: dict[str, Any]
) -> dict[str, TimeEntryVerification]:
    results: dict[str, TimeEntryVerification] = {}
    for field, value in expected.items():
        source = REFERENCE_FIELDS.get(field, field)
        if source not in actual or actual[source] is None:
            results[field] = "unavailable"
            continue
        observed = (
            item(TimeEntryIssueReference, actual[source]).id
            if field in REFERENCE_FIELDS
            else actual[source]
        )
        if field == "hours":
            observed = Decimal(str(observed))
        results[field] = "matched" if observed == value else "mismatch"
    return results


class RedmineTimeEntryCreations:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def create_time_entry(
        self, issue_id: int, request: TimeEntryCreateRequest, caller_id: int
    ) -> TimeEntryCreateResult:
        issue_data = await self.client.get(f"issues/{issue_id}.json", {"include": ""})
        issue = resource_object(issue_data.get("issue"), issue_id)
        project_id = item(TimeEntryIssueReference, issue.get("project")).id
        payload = request.model_dump(mode="json", exclude_unset=True)
        payload.update(project_id=project_id, issue_id=issue_id)
        expected = {**payload, "user_id": caller_id, "hours": normalized_hours(request.hours)}
        receipt = await self.writer.write_json(
            HTTPMethod.POST,
            "time_entries.json",
            {"time_entry": payload},
            accepted_statuses=(http_status.HTTP_201_CREATED,),
            params={"project_id": str(project_id)},
        )
        result = TimeEntryCreateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_201_CREATED else None,
            field_verification={field: "unavailable" for field in expected},
        )
        created = receipt.payload.get("time_entry") if receipt.payload is not None else None
        entry_id = created.get("id") if isinstance(created, dict) else None
        if type(entry_id) is not int or entry_id < 1:
            result.outcome = "uncertain"
            return result
        result.resource_id = entry_id
        try:
            observed_creation = map_time_entry(resource_object(created, entry_id))
            if (
                observed_creation.project.id != project_id
                or observed_creation.issue_id != issue_id
                or observed_creation.user.id != caller_id
            ):
                result.outcome = "uncertain"
        except ApplicationError:
            result.outcome = "uncertain"

        try:
            data = await self.client.get(f"time_entries/{entry_id}.json", {})
            actual = resource_object(data.get("time_entry"), entry_id)
            observed = map_time_entry(actual)
            fields = verify_fields(actual, expected)
        except ApplicationError:
            return result
        result.observed_time_entry = observed
        result.field_verification = fields
        if "mismatch" in fields.values():
            result.verification = "mismatch"
        elif "unavailable" not in fields.values():
            result.verification = "matched"
        return result
