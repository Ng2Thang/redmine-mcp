"""Delegate creation/copy to Redmine and independently inspect supplied fields."""

from typing import Any

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.issues.models import ISSUE_INCLUDES, IssueDetail
from redmine_mcp.features.issues.write_models import (
    IssueCreateRequest,
    IssueCreateResult,
    Verification,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.mapping import item, visible_item
from redmine_mcp.integrations.redmine.responses import resource_object
from redmine_mcp.integrations.redmine.write import RedmineWriter

REFERENCE_FIELDS = {
    "project_id": "project",
    "tracker_id": "tracker",
    "status_id": "status",
    "priority_id": "priority",
    "category_id": "category",
    "fixed_version_id": "fixed_version",
    "assigned_to_id": "assigned_to",
    "parent_issue_id": "parent",
}


def compare_value(actual: Any, expected: Any) -> Verification:
    if isinstance(actual, list) and isinstance(expected, list):

        def sort_key(value: Any) -> tuple[str, str]:
            return type(value).__name__, str(value)

        return (
            "matched"
            if sorted(actual, key=sort_key) == sorted(expected, key=sort_key)
            else "mismatch"
        )
    return "matched" if actual == expected else "mismatch"


def verify_custom_fields(actual: dict[str, Any], expected: list[dict[str, Any]]) -> Verification:
    if not expected:
        return "matched"
    values = actual.get("custom_fields")
    if not isinstance(values, list):
        return "unavailable"
    outcomes: list[Verification] = []
    for field in expected:
        observed = next((value for value in values if value.get("id") == field["id"]), None)
        outcomes.append(
            "unavailable"
            if observed is None or "value" not in observed
            else compare_value(observed["value"], field["value"])
        )
    return aggregate_verification(outcomes)


def verify_uploads(actual: dict[str, Any], expected: list[dict[str, Any]]) -> Verification:
    if not expected:
        return "matched"
    values = actual.get("attachments")
    if not isinstance(values, list):
        return "unavailable"
    outcomes: list[Verification] = []
    for upload in expected:
        attachment_id = int(upload["token"].split(".", 1)[0])
        observed = next((value for value in values if value.get("id") == attachment_id), None)
        if observed is None:
            outcomes.append("mismatch")
            continue
        for field in ("filename", "description", "content_type"):
            if field not in upload:
                continue
            expected_value = upload[field].strip() if field == "description" else upload[field]
            outcomes.append(
                "unavailable"
                if field not in observed
                else compare_value(observed[field], expected_value)
            )
    return aggregate_verification(outcomes)


def aggregate_verification(outcomes: list[Verification]) -> Verification:
    if "mismatch" in outcomes:
        return "mismatch"
    if "unavailable" in outcomes:
        return "unavailable"
    return "matched"


def verify_creation_fields(
    actual: dict[str, Any], expected: dict[str, Any]
) -> dict[str, Verification]:
    results: dict[str, Verification] = {}
    for field, value in expected.items():
        if field in REFERENCE_FIELDS:
            reference = actual.get(REFERENCE_FIELDS[field])
            if reference is None:
                # Exact 7.0.2 omits optional references when unset.
                results[field] = "matched" if value is None else "mismatch"
            else:
                results[field] = compare_value(reference.get("id"), value)
        elif field == "custom_fields":
            results[field] = verify_custom_fields(actual, value)
        elif field == "uploads":
            results[field] = verify_uploads(actual, value)
        elif field == "watcher_user_ids":
            watchers = actual.get("watchers")
            results[field] = (
                "unavailable"
                if not isinstance(watchers, list)
                else compare_value([watcher["id"] for watcher in watchers], value)
            )
        else:
            results[field] = (
                "unavailable" if field not in actual else compare_value(actual[field], value)
            )
    return results


class RedmineIssueCreations:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def create_issue(self, request: IssueCreateRequest) -> IssueCreateResult:
        if request.copy_from is not None:
            source = await self.client.get(f"issues/{request.copy_from}.json", {})
            item(IssueDetail, resource_object(source.get("issue"), request.copy_from))
        expected = request.model_dump(mode="json", exclude_unset=True, exclude={"copy_from"})
        if request.assigned_to_id == "me":
            identity = await self.client.get("users/current.json", {})
            user = identity.get("user")
            user_id = user.get("id") if isinstance(user, dict) else None
            resource_object(user, user_id if type(user_id) is int and user_id > 0 else -1)
            expected["assigned_to_id"] = user_id
        params = {"project_id": str(request.project_id)}
        if request.copy_from is not None:
            params["copy_from"] = str(request.copy_from)
        payload = request.model_dump(mode="json", exclude_unset=True, exclude={"copy_from"})
        if "assigned_to_id" in payload and payload["assigned_to_id"] is None:
            # Preserve explicit clearing when copying an assigned issue on Redmine 7.0.2.
            payload["assigned_to_id"] = ""
        receipt = await self.writer.write_json(
            "POST",
            "issues.json",
            {"issue": payload},
            accepted_statuses=(http_status.HTTP_201_CREATED,),
            params=params,
        )
        issue = receipt.payload.get("issue") if receipt.payload is not None else None
        resource_id = issue.get("id") if isinstance(issue, dict) else None
        result = IssueCreateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_201_CREATED else None,
            field_verification={field: "unavailable" for field in expected},
        )
        if type(resource_id) is not int or resource_id < 1:
            result.outcome = "uncertain"
            return result
        result.resource_id = resource_id
        includes = []
        if request.uploads is not None:
            includes.append("attachments")
        if request.watcher_user_ids is not None:
            includes.append("watchers")
        read_params: dict[str, str | int] = {"include": ",".join(includes)} if includes else {}
        try:
            data = await self.client.get(f"issues/{resource_id}.json", read_params)
            actual = resource_object(data.get("issue"), resource_id)
            fields = [REFERENCE_FIELDS.get(field, field) for field in expected]
            fields = ["attachments" if field == "uploads" else field for field in fields]
            fields = ["watchers" if field == "watcher_user_ids" else field for field in fields]
            result.observed_issue = visible_item(
                IssueDetail,
                actual,
                observed_fields=[field for field in fields if field not in includes],
                requested_fields=includes,
                unrequested_fields=sorted(ISSUE_INCLUDES.difference(includes)),
            )
        except ApplicationError:
            return result
        result.field_verification = verify_creation_fields(actual, expected)
        result.verification = aggregate_verification(list(result.field_verification.values()))
        return result
