"""WRT-04: visible journal membership and truthful note/privacy read-back."""

import copy
import json
from typing import Any

import httpx
import pytest

from tests.issue_write_helpers import assert_error, invoke, override, writes

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "payload",
    [
        {"notes": ""},
        {"notes": "exact edited note"},
        {"private_notes": True},
        {"notes": "combined", "private_notes": False},
    ],
)
async def test_same_journal_update_preserves_omitted_fields(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    payload: dict[str, Any],
) -> None:
    before = copy.deepcopy(synthetic.issues[42]["journals"][0])
    status, data = await invoke(
        writer_app,
        boundary,
        "update_issue_note",
        {
            "issue_id": 42,
            "journal_id": 1,
            **payload,
        },
    )
    assert status == 200 and data["outcome"] == "accepted"
    assert data["upstream_accepted"] is True and data["verification"] == "matched"
    assert data["resource_id"] == 1 and data["observed_present"] is True
    assert data["field_verification"] == {field: "matched" for field in payload}
    assert synthetic.issues[42]["journals"][0] == before | payload
    assert len(writes(synthetic)) == 1
    request = writes(synthetic)[0]
    assert (request.method, request.url.path) == ("PUT", "/journals/1.json")
    assert json.loads(request.content) == {"journal": payload}
    assert not request.url.params


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "fault,code",
    [
        ("other_issue", "resource_not_found"),
        ("invisible", "resource_not_found"),
        ("missing_list", "upstream_response"),
        ("duplicate", "upstream_response"),
        ("boolean_id", "upstream_response"),
        ("invalid_privacy", "upstream_response"),
    ],
)
async def test_journal_proof_failures_never_write(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    fault: str,
    code: str,
) -> None:
    journal = copy.deepcopy(synthetic.issues[42]["journals"][0])
    if fault == "other_issue":
        synthetic.issues[43]["journals"] = [journal]
        synthetic.issues[42]["journals"] = []
    elif fault == "invisible":
        synthetic.issues[42]["journals"] = []
    elif fault == "missing_list":
        synthetic.issues[42].pop("journals")
    elif fault == "duplicate":
        synthetic.issues[42]["journals"].append(journal)
    elif fault == "boolean_id":
        synthetic.issues[42]["journals"][0]["id"] = True
    else:
        synthetic.issues[42]["journals"][0]["private_notes"] = "false"
    before = copy.deepcopy(synthetic.issues)
    status, data = await invoke(
        writer_app,
        boundary,
        "update_issue_note",
        {
            "issue_id": 42,
            "journal_id": 1,
            "notes": "must not be written",
        },
    )
    assert status == (422 if boundary == "mcp" else 404 if code == "resource_not_found" else 502)
    assert_error(data, boundary, code)
    assert writes(synthetic) == [] and synthetic.issues == before


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize(
    "fault,verification,present",
    [
        ("hidden", "unavailable", False),
        ("forbidden", "unavailable", None),
        ("missing_notes", "unavailable", True),
        ("ignored_notes", "mismatch", True),
        ("ignored_privacy", "mismatch", True),
    ],
)
async def test_accepted_note_write_survives_hidden_unreadable_and_ignored_fields(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
    fault: str,
    verification: str,
    present: bool | None,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response | None:
        if synthetic.writes and request.url.path == "/issues/42.json":
            if fault == "forbidden":
                return httpx.Response(403)
            issue = copy.deepcopy(synthetic.issues[42])
            journal = issue["journals"][0]
            if fault == "hidden":
                issue["journals"] = []
            elif fault == "missing_notes":
                journal.pop("notes")
            elif fault == "ignored_notes":
                journal["notes"] = "ignored"
            else:
                journal["private_notes"] = False
            return httpx.Response(200, json={"issue": issue})
        return None

    override(synthetic, respond)
    status, data = await invoke(
        writer_app,
        boundary,
        "update_issue_note",
        {
            "issue_id": 42,
            "journal_id": 1,
            "notes": "",
            "private_notes": True,
        },
    )
    assert status == 200 and data["outcome"] == "accepted" and data["upstream_accepted"] is True
    assert data["verification"] == verification and data["observed_present"] is present
    assert synthetic.issues[42]["journals"][0]["notes"] == ""
    assert len(writes(synthetic)) == 1
    if fault == "missing_notes":
        assert data["field_verification"] == {"notes": "unavailable", "private_notes": "matched"}


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_native_privacy_rejection_is_not_local_success(
    writer_app: Any,
    synthetic: Any,
    boundary: str,
) -> None:
    before = copy.deepcopy(synthetic.issues[42]["journals"])
    synthetic.write_failure = 403
    status, data = await invoke(
        writer_app,
        boundary,
        "update_issue_note",
        {
            "issue_id": 42,
            "journal_id": 1,
            "private_notes": True,
        },
    )
    assert status == (403 if boundary == "rest" else 422)
    assert_error(data, boundary, "access_denied")
    assert synthetic.issues[42]["journals"] == before and len(writes(synthetic)) == 1
    assert "must-not-leak" not in json.dumps(data)
