"""Delete one issue-bound entry and report caller-visible presence independently."""

from http import HTTPMethod

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.time_entries.write_models import TimeEntryDeleteResult
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.responses import resource_object
from redmine_mcp.integrations.redmine.time_entries import map_time_entry
from redmine_mcp.integrations.redmine.time_entry_updates import require_issue_time_entry
from redmine_mcp.integrations.redmine.write import RedmineWriter


class RedmineTimeEntryDeletions:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def delete_time_entry(self, issue_id: int, time_entry_id: int) -> TimeEntryDeleteResult:
        await require_issue_time_entry(self.client, issue_id, time_entry_id)
        receipt = await self.writer.write_json(
            HTTPMethod.DELETE,
            f"time_entries/{time_entry_id}.json",
            accepted_statuses=(http_status.HTTP_204_NO_CONTENT,),
        )
        # A received native 204 confirms acceptance even if response cleanup later fails.
        accepted = receipt.status == http_status.HTTP_204_NO_CONTENT
        result = TimeEntryDeleteResult(
            outcome="accepted" if accepted else receipt.outcome,
            upstream_accepted=True if accepted else None,
            resource_id=time_entry_id,
            issue_id=issue_id,
        )
        try:
            data = await self.client.get(f"time_entries/{time_entry_id}.json", {})
            map_time_entry(resource_object(data.get("time_entry"), time_entry_id))
        except ApplicationError as error:
            if error.status == http_status.HTTP_404_NOT_FOUND:
                result.verification = "not_found"
                result.observed_present = False
            return result
        result.verification = "still_present"
        result.observed_present = True
        return result
