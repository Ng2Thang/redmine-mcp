"""WRT-01/02/07: independent relation receipts and two-endpoint deletion proofs."""

import copy
import json
from typing import Any

import httpx
import pytest

from tests.issue_write_helpers import (
    RELATION_CASES,
    assert_error,
    invoke,
    override,
    writes,
)

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("source,target,kind,delay,stored", RELATION_CASES)
async def test_relation_normalization_and_exact_original_payload(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    source: int,
    target: int,
    kind: str,
    delay: int | None,
    stored: tuple[Any, ...],
) -> None:
    payload = {"issue_to_id": target, "relation_type": kind}
    if delay is not None:
        payload["delay"] = delay
    status, data = await invoke(
        writer_app,
        boundary,
        "create_issue_relation",
        {
            "issue_id": source,
            **payload,
        },
    )
    assert status == 200 and data["outcome"] == "accepted"
    assert data["upstream_accepted"] is True and data["verification"] == "matched"
    observed = data["observed_relation"]
    assert [observed[k] for k in ("issue_id", "issue_to_id", "relation_type", "delay")] == list(
        stored
    )
    assert data["field_verification"] == {
        "issue_id": "matched",
        "issue_to_id": "matched",
        "relation_type": "matched",
        "delay": "matched",
    }
    dispatched = writes(synthetic)
    assert len(dispatched) == 1
    assert dispatched[0].method == "POST"
    assert dispatched[0].url.path == f"/issues/{source}/relations.json"
    assert json.loads(dispatched[0].content) == {"relation": payload}
    assert dispatched[0].headers["X-Redmine-API-Key"] == "offline-redmine-key"
    assert (
        synthetic.issues[42]["relations"]
        == synthetic.issues[43]["relations"]
        == [synthetic.relation]
    )


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_default_relation_and_self_link_rejection(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
) -> None:
    status, data = await invoke(
        writer_app,
        boundary,
        "create_issue_relation",
        {
            "issue_id": 42,
            "issue_to_id": 43,
        },
    )
    assert status == 200 and data["verification"] == "matched"
    assert json.loads(writes(synthetic)[0].content) == {
        "relation": {"issue_to_id": 43, "relation_type": "relates"}
    }
    status, data = await invoke(
        writer_app,
        boundary,
        "create_issue_relation",
        {
            "issue_id": 42,
            "issue_to_id": 42,
        },
    )
    assert status == 422
    assert_error(data, boundary, "invalid_parameters")
    assert len(writes(synthetic)) == 1


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "fault,code",
    [
        ("duplicate", "upstream_response"),
        ("malformed", "upstream_response"),
        ("wrong_endpoint", "upstream_response"),
        ("absent", "resource_not_found"),
        ("inaccessible", "access_denied"),
        ("self_endpoint", "upstream_response"),
    ],
)
async def test_delete_requires_both_valid_endpoint_proofs_before_dispatch(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    fault: str,
    code: str,
) -> None:
    for issue in synthetic.issues.values():
        issue["relations"] = [copy.deepcopy(synthetic.relation)]
    if fault == "self_endpoint":
        synthetic.relation["issue_to_id"] = 42
    elif fault != "inaccessible":
        relations = synthetic.issues[43]["relations"]
        if fault == "duplicate":
            relations.append(copy.deepcopy(relations[0]))
        elif fault == "malformed":
            relations[0]["id"] = True
        elif fault == "wrong_endpoint":
            relations[0].update(issue_id=44, issue_to_id=45)
        else:
            relations.clear()
    else:
        override(
            synthetic,
            lambda r: (
                httpx.Response(403)
                if r.url.path == "/issues/43.json" and r.url.params.get("include") == "relations"
                else None
            ),
        )
    status, data = await invoke(writer_app, boundary, "delete_issue_relation", {"relation_id": 1})
    assert status == (
        422
        if boundary == "mcp"
        else {
            "upstream_response": 502,
            "resource_not_found": 404,
            "access_denied": 403,
        }[code]
    )
    assert_error(data, boundary, code)
    assert synthetic.writes == 0 and writes(synthetic) == []


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "observations,verification,present",
    [
        ((False, False), "matched", False),
        ((True, False), "mismatch", True),
        ((False, True), "mismatch", True),
        ((None, False), "unavailable", None),
        ((None, None), "unavailable", None),
    ],
)
async def test_delete_preserves_independent_endpoint_observations(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    observations: tuple[bool | None, bool | None],
    verification: str,
    present: bool | None,
) -> None:
    relation = copy.deepcopy(synthetic.relation)
    for issue in synthetic.issues.values():
        issue["relations"] = [copy.deepcopy(relation)]

    def respond(request: httpx.Request) -> httpx.Response | None:
        if synthetic.writes and request.url.path in ("/issues/42.json", "/issues/43.json"):
            issue_id = int(request.url.path.split("/")[2].split(".")[0])
            observation = observations[0 if issue_id == 42 else 1]
            if observation is None:
                return httpx.Response(403)
            return httpx.Response(
                200,
                json={
                    "issue": {
                        **synthetic.issues[issue_id],
                        "relations": [relation] if observation else [],
                    }
                },
            )
        return None

    override(synthetic, respond)
    status, data = await invoke(writer_app, boundary, "delete_issue_relation", {"relation_id": 1})
    assert status == 200 and data["outcome"] == "accepted" and data["upstream_accepted"] is True
    assert data["endpoint_observations"] == dict(zip(("42", "43"), observations, strict=True))
    assert data["verification"] == verification and data["observed_present"] is present
    assert len(writes(synthetic)) == 1 and writes(synthetic)[0].content == b""


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("fault", ["missing_id", "boolean_id", "mismatch", "missing_delay"])
async def test_creation_receipt_identity_and_missing_observation_are_not_invented(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    fault: str,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response | None:
        if request.method == "POST":
            identifier = None if fault == "missing_id" else True if fault == "boolean_id" else 1
            return httpx.Response(201, json={"relation": {"id": identifier}})
        if synthetic.writes and request.url.path == "/relations/1.json":
            relation = {**synthetic.relation, "relation_type": "precedes", "delay": 0}
            if fault == "mismatch":
                relation["delay"] = 3
            else:
                relation.pop("delay")
            return httpx.Response(200, json={"relation": relation})
        return None

    override(synthetic, respond)
    status, data = await invoke(
        writer_app,
        boundary,
        "create_issue_relation",
        {
            "issue_id": 42,
            "issue_to_id": 43,
            "relation_type": "precedes",
        },
    )
    assert status == 200 and data["upstream_accepted"] is True
    assert data["outcome"] == ("uncertain" if fault.endswith("id") else "accepted")
    assert data["verification"] == ("mismatch" if fault == "mismatch" else "unavailable")
    assert data["resource_id"] == (None if fault.endswith("id") else 1)
    assert len(writes(synthetic)) == 1
    if fault.endswith("id"):
        after = synthetic.requests[synthetic.requests.index(writes(synthetic)[0]) + 1 :]
        assert not any(r.url.path.startswith("/relations/") for r in after)
