"""Create a single relation and verify Redmine's normalized stored direction."""

from http import HTTPMethod
from typing import Any

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.issues.write_models import (
    IssueRelationCreateRequest,
    IssueRelationCreateResult,
    IssueRelationDeleteResult,
    RelationObservation,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.issue_creations import aggregate_verification, compare_value
from redmine_mcp.integrations.redmine.mapping import item, visible_item
from redmine_mcp.integrations.redmine.responses import resource_object, response_items
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

    async def _contains_relation(self, issue_id: int, relation_id: int) -> bool:
        data = await self.client.get(f"issues/{issue_id}.json", {"include": "relations"})
        issue = resource_object(data.get("issue"), issue_id)
        # The pinned issue API omits this requested list when no visible relations remain.
        if "relations" not in issue:
            return False
        seen: set[int] = set()
        for raw in response_items(issue, "relations"):
            relation = item(RelationObservation, raw)
            if relation.id in seen or issue_id not in (relation.issue_id, relation.issue_to_id):
                raise ApplicationError(
                    codes_text.UPSTREAM_RESPONSE,
                    redmine_text.UNEXPECTED_DATA,
                    http_status.HTTP_502_BAD_GATEWAY,
                )
            seen.add(relation.id)
        return relation_id in seen

    async def delete_issue_relation(self, relation_id: int) -> IssueRelationDeleteResult:
        data = await self.client.get(f"relations/{relation_id}.json", {})
        resolved = visible_item(
            RelationObservation,
            resource_object(data.get("relation"), relation_id),
            observed_fields=("issue_id", "issue_to_id", "relation_type", "delay"),
        )
        endpoints = (resolved.issue_id, resolved.issue_to_id)
        if endpoints[0] == endpoints[1]:
            raise ApplicationError(
                codes_text.UPSTREAM_RESPONSE,
                redmine_text.UNEXPECTED_DATA,
                http_status.HTTP_502_BAD_GATEWAY,
            )
        for endpoint in endpoints:
            if not await self._contains_relation(endpoint, relation_id):
                raise ApplicationError(
                    codes_text.RESOURCE_NOT_FOUND,
                    redmine_text.RESOURCE_UNAVAILABLE,
                    http_status.HTTP_404_NOT_FOUND,
                )
        receipt = await self.writer.write_json(
            HTTPMethod.DELETE,
            f"relations/{relation_id}.json",
            accepted_statuses=(http_status.HTTP_204_NO_CONTENT,),
        )
        result = IssueRelationDeleteResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_204_NO_CONTENT else None,
            resource_id=relation_id,
            resolved_relation=resolved,
            endpoint_observations={str(endpoint): None for endpoint in endpoints},
        )
        for endpoint in endpoints:
            try:
                result.endpoint_observations[str(endpoint)] = await self._contains_relation(
                    endpoint, relation_id
                )
            except ApplicationError:
                continue
        observations = tuple(result.endpoint_observations.values())
        if any(present is True for present in observations):
            result.observed_present = True
            result.verification = "mismatch"
        elif all(present is False for present in observations):
            result.observed_present = False
            result.verification = "matched"
        return result

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
            HTTPMethod.POST,
            f"issues/{issue_id}/relations.json",
            {"relation": payload},
            accepted_statuses=(http_status.HTTP_201_CREATED,),
        )
        result = IssueRelationCreateResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_201_CREATED else None,
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
