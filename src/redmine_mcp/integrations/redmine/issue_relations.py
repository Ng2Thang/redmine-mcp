"""Create a single relation and verify Redmine's normalized stored direction."""

from typing import Any

from redmine_mcp.common import ApplicationError
from redmine_mcp.features.issues.write_models import (
    IssueRelationCreateRequest,
    IssueRelationCreateResult,
    RelationObservation,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.issue_creations import aggregate_verification, compare_value
from redmine_mcp.integrations.redmine.mapping import visible_item
from redmine_mcp.integrations.redmine.responses import resource_object
from redmine_mcp.integrations.redmine.write import RedmineWriter


def expected_relation(issue_id: int, request: IssueRelationCreateRequest) -> dict[str, Any]:
    source, target = issue_id, request.issue_to_id
    relation_type: str = request.relation_type
    inverse = {
        "duplicated": "duplicates",
        "blocked": "blocks",
        "follows": "precedes",
        "copied_from": "copied_to",
    }
    if relation_type in inverse:
        source, target = target, source
        relation_type = inverse[relation_type]
    elif relation_type == "relates" and source > target:
        source, target = target, source
    return {
        "issue_id": source,
        "issue_to_id": target,
        "relation_type": relation_type,
        "delay": (request.delay if request.delay is not None else 0)
        if relation_type == "precedes"
        else None,
    }


class RedmineIssueRelations:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def create_issue_relation(
        self, issue_id: int, request: IssueRelationCreateRequest
    ) -> IssueRelationCreateResult:
        for visible_id in (issue_id, request.issue_to_id):
            data = await self.client.get(f"issues/{visible_id}.json", {})
            resource_object(data.get("issue"), visible_id)
        expected = expected_relation(issue_id, request)
        payload = request.model_dump(mode="json", exclude_unset=True)
        payload["relation_type"] = request.relation_type
        receipt = await self.writer.write_json(
            "POST",
            f"issues/{issue_id}/relations.json",
            {"relation": payload},
            accepted_statuses=(201,),
        )
        result = IssueRelationCreateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == 201 else None,
            field_verification={field: "unavailable" for field in expected},
        )
        created = (receipt.payload or {}).get("relation")
        if not isinstance(created, dict) or type(created.get("id")) is not int or created["id"] < 1:
            result.outcome = "uncertain"
            return result
        relation_id: int = created["id"]
        result.resource_id = relation_id
        try:
            data = await self.client.get(f"relations/{relation_id}.json", {})
            observed = resource_object(data.get("relation"), relation_id)
            result.observed_relation = visible_item(
                RelationObservation, observed, observed_fields=tuple(expected)
            )
        except ApplicationError:
            return result
        for field, value in expected.items():
            if field in observed and type(observed[field]) is type(value):
                result.field_verification[field] = compare_value(observed[field], value)
        result.verification = aggregate_verification(list(result.field_verification.values()))
        return result
