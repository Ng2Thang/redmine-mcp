"""Update supplied issue attributes and observe fields and newly added notes."""

from http import HTTPMethod
from typing import Any

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.issues.models import ISSUE_INCLUDES, IssueDetail, Journal
from redmine_mcp.features.issues.write_models import IssueUpdateRequest, IssueUpdateResult
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.issue_creations import (
    REFERENCE_FIELDS,
    aggregate_verification,
    compare_value,
    verify_creation_fields,
)
from redmine_mcp.integrations.redmine.mapping import item, visible_item
from redmine_mcp.integrations.redmine.responses import (
    resource_object,
    response_items,
    response_object,
)
from redmine_mcp.integrations.redmine.write import RedmineWriter


def journal_ids(issue: dict[str, Any]) -> set[int]:
    ids: set[int] = set()
    for journal in response_items(issue, "journals"):
        journal_id = item(Journal, journal).id
        if journal_id in ids:
            raise ApplicationError(
                codes_text.UPSTREAM_RESPONSE,
                redmine_text.UNEXPECTED_DATA,
                http_status.HTTP_502_BAD_GATEWAY,
            )
        ids.add(journal_id)
    return ids


def verify_new_note(
    actual: dict[str, Any],
    before_ids: set[int],
    caller_id: int | None,
    request: IssueUpdateRequest,
    result: IssueUpdateResult,
) -> None:
    candidates = [
        journal
        for journal in actual["journals"]
        if journal["id"] not in before_ids
        and isinstance(journal.get("user"), dict)
        and type(journal["user"].get("id")) is int
        and journal["user"]["id"] == caller_id
    ]
    matches = [journal for journal in candidates if journal.get("notes") == request.notes]
    if len(matches) == 1:
        observed = matches[0]
    elif not matches and len(candidates) == 1:
        observed = candidates[0]
    else:
        return
    result.journal_id = observed["id"]
    if "notes" in observed:
        result.field_verification["notes"] = compare_value(observed["notes"], request.notes)
    if request.private_notes is not None and type(observed.get("private_notes")) is bool:
        result.field_verification["private_notes"] = compare_value(
            observed["private_notes"], request.private_notes
        )


class RedmineIssueUpdates:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def _caller_id(self) -> int:
        data = await self.client.get("users/current.json", {})
        user = response_object(data.get("user"))
        user_id = user.get("id")
        if type(user_id) is not int or user_id < 1:
            raise ApplicationError(
                codes_text.UPSTREAM_RESPONSE,
                redmine_text.UNEXPECTED_DATA,
                http_status.HTTP_502_BAD_GATEWAY,
            )
        return user_id

    async def update_issue(self, issue_id: int, request: IssueUpdateRequest) -> IssueUpdateResult:
        preflight_params: dict[str, str | int] = (
            {"include": "journals"} if request.notes is not None else {}
        )
        before = await self.client.get(f"issues/{issue_id}.json", preflight_params)
        before_issue = resource_object(before.get("issue"), issue_id)
        # Validate before dispatch; retain raw fields for presence and journal comparisons.
        item(IssueDetail, before_issue)
        before_ids = journal_ids(before_issue) if request.notes is not None else set()
        caller_id = (
            await self._caller_id()
            if request.notes is not None or request.assigned_to_id == "me"
            else None
        )
        payload = request.model_dump(mode="json", exclude_unset=True)
        expected = {
            key: value for key, value in payload.items() if key not in ("notes", "private_notes")
        }
        if request.assigned_to_id == "me":
            expected["assigned_to_id"] = caller_id
        if "assigned_to_id" in payload and payload["assigned_to_id"] is None:
            # Redmine 7.0.2 ignores nil in safe_attributes=; an empty ID clears assignment.
            payload["assigned_to_id"] = ""
        receipt = await self.writer.write_json(
            HTTPMethod.PUT,
            f"issues/{issue_id}.json",
            {"issue": payload},
            accepted_statuses=(http_status.HTTP_204_NO_CONTENT,),
        )
        result = IssueUpdateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_204_NO_CONTENT else None,
            resource_id=issue_id,
            field_verification={field: "unavailable" for field in payload},
        )
        includes = []
        if request.uploads is not None:
            includes.append("attachments")
        if request.notes is not None:
            includes.append("journals")
        read_params: dict[str, str | int] = {"include": ",".join(includes)} if includes else {}
        try:
            data = await self.client.get(f"issues/{issue_id}.json", read_params)
            actual = resource_object(data.get("issue"), issue_id)
            fields = [REFERENCE_FIELDS.get(field, field) for field in expected]
            fields = ["attachments" if field == "uploads" else field for field in fields]
            result.observed_issue = visible_item(
                IssueDetail,
                actual,
                observed_fields=[field for field in fields if field not in includes],
                requested_fields=includes,
                unrequested_fields=sorted(ISSUE_INCLUDES.difference(includes)),
            )
            result.field_verification.update(verify_creation_fields(actual, expected))
            if request.notes is not None:
                journal_ids(actual)
                verify_new_note(actual, before_ids, caller_id, request, result)
        except ApplicationError:
            result.verification = aggregate_verification(list(result.field_verification.values()))
            return result
        result.verification = aggregate_verification(list(result.field_verification.values()))
        return result
