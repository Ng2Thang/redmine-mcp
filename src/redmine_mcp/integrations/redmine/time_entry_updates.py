"""Update one issue-bound entry with a single PUT and independent verification."""

from http import HTTPMethod

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError, InvalidInputError
from redmine_mcp.features.time_entries.models import TimeEntry, TimeEntryIssueReference
from redmine_mcp.features.time_entries.write_models import (
    TimeEntryUpdateRequest,
    TimeEntryUpdateResult,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item
from redmine_mcp.integrations.redmine.responses import resource_object
from redmine_mcp.integrations.redmine.time_entries import map_time_entry
from redmine_mcp.integrations.redmine.time_entry_creations import normalized_hours, verify_fields
from redmine_mcp.integrations.redmine.write import RedmineWriter


async def require_issue_time_entry(
    client: RedmineClient, issue_id: int, time_entry_id: int
) -> TimeEntry:
    """Validate visible exact identities for both capability resolution and dispatch."""
    data = await client.get(f"time_entries/{time_entry_id}.json", {})
    entry = map_time_entry(resource_object(data.get("time_entry"), time_entry_id))
    issue_data = await client.get(f"issues/{issue_id}.json", {"include": ""})
    issue = resource_object(issue_data.get("issue"), issue_id)
    project_id = item(TimeEntryIssueReference, issue.get("project")).id
    if entry.issue_id != issue_id or entry.project.id != project_id:
        raise InvalidInputError("Time entry does not belong to the selected issue and project")
    return entry


class RedmineTimeEntryUpdates:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def update_time_entry(
        self, issue_id: int, time_entry_id: int, request: TimeEntryUpdateRequest
    ) -> TimeEntryUpdateResult:
        entry = await require_issue_time_entry(self.client, issue_id, time_entry_id)
        payload = request.model_dump(mode="json", exclude_unset=True)
        expected = {
            **payload,
            "issue_id": issue_id,
            "project_id": entry.project.id,
            "user_id": entry.user.id,
        }
        if request.hours is not None:
            expected["hours"] = normalized_hours(request.hours)
        receipt = await self.writer.write_json(
            HTTPMethod.PUT,
            f"time_entries/{time_entry_id}.json",
            {"time_entry": payload},
            accepted_statuses=(http_status.HTTP_204_NO_CONTENT,),
        )
        result = TimeEntryUpdateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_204_NO_CONTENT else None,
            resource_id=time_entry_id,
            issue_id=issue_id,
            field_verification={field: "unavailable" for field in expected},
        )
        try:
            data = await self.client.get(f"time_entries/{time_entry_id}.json", {})
            actual = resource_object(data.get("time_entry"), time_entry_id)
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
