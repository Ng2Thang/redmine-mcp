"""Edit a visible issue journal without bypassing its declared issue membership."""

from typing import Any

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.issues.write_models import (
    IssueNoteUpdateRequest,
    IssueNoteUpdateResult,
    JournalObservation,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.issue_creations import aggregate_verification, compare_value
from redmine_mcp.integrations.redmine.issue_updates import journal_ids
from redmine_mcp.integrations.redmine.mapping import visible_item
from redmine_mcp.integrations.redmine.responses import resource_object, response_items
from redmine_mcp.integrations.redmine.write import RedmineWriter


class RedmineIssueNotes:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def _visible_journal(self, issue_id: int, journal_id: int) -> dict[str, Any] | None:
        data = await self.client.get(f"issues/{issue_id}.json", {"include": "journals"})
        issue = resource_object(data.get("issue"), issue_id)
        journal_ids(issue)
        return next(
            (
                journal
                for journal in response_items(issue, "journals")
                if journal["id"] == journal_id
            ),
            None,
        )

    async def update_issue_note(
        self, issue_id: int, journal_id: int, request: IssueNoteUpdateRequest
    ) -> IssueNoteUpdateResult:
        before = await self._visible_journal(issue_id, journal_id)
        if before is None:
            raise ApplicationError(
                codes_text.RESOURCE_NOT_FOUND, redmine_text.RESOURCE_UNAVAILABLE, 404
            )
        # Validate the target before dispatch; default model values never prove field presence.
        visible_item(
            JournalObservation, before, observed_fields=("notes", "private_notes", "details")
        )
        payload = request.model_dump(mode="json", exclude_unset=True)
        receipt = await self.writer.write_json(
            "PUT", f"journals/{journal_id}.json", {"journal": payload}, accepted_statuses=(204,)
        )
        result = IssueNoteUpdateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == 204 else None,
            issue_id=issue_id,
            resource_id=journal_id,
            field_verification={field: "unavailable" for field in payload},
        )
        try:
            observed = await self._visible_journal(issue_id, journal_id)
            result.observed_present = observed is not None
            if observed is None:
                return result
            result.observed_journal = visible_item(
                JournalObservation, observed, observed_fields=tuple(payload)
            )
        except ApplicationError:
            return result
        for field, expected in payload.items():
            if field in observed and type(observed[field]) is type(expected):
                result.field_verification[field] = compare_value(observed[field], expected)
        result.verification = aggregate_verification(list(result.field_verification.values()))
        return result
