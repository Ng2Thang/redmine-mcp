"""WRT-01: normalization expectations come from literal native fixtures."""

from typing import Any

import pytest

from redmine_mcp.features.issues.write_models import IssueRelationCreateRequest
from redmine_mcp.integrations.redmine.issue_relations import expected_relation
from tests.issue_write_helpers import RELATION_CASES, RELATION_RESPONSES


@pytest.mark.parametrize("source,target,kind,delay,stored", RELATION_CASES)
def test_native_direction_order_and_signed_delay(
    source: int, target: int, kind: str, delay: int | None, stored: tuple[Any, ...]
) -> None:
    arguments = {"issue_to_id": target, "relation_type": kind}
    if delay is not None:
        arguments["delay"] = delay
    request = IssueRelationCreateRequest(**arguments)
    actual = expected_relation(source, request)
    assert actual == {
        "issue_id": stored[0],
        "issue_to_id": stored[1],
        "relation_type": stored[2],
        "delay": stored[3],
    }
    assert actual == RELATION_RESPONSES[(source, target, kind, delay)]
