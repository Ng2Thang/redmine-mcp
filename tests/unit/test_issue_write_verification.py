"""WRT-06: distinguish observed fields, omission and ambiguous journal attribution."""

from typing import Any

import pytest

from redmine_mcp.features.issues.write_models import IssueUpdateRequest, IssueUpdateResult
from redmine_mcp.integrations.redmine.issue_creations import (
    aggregate_verification,
    verify_creation_fields,
    verify_custom_fields,
    verify_uploads,
)
from redmine_mcp.integrations.redmine.issue_updates import verify_new_note


@pytest.mark.parametrize(
    "actual,expected,outcome",
    [
        ({"custom_fields": [{"id": 1, "value": "text"}]}, [{"id": 1, "value": "text"}], "matched"),
        ({"custom_fields": [{"id": 1, "value": None}]}, [{"id": 1, "value": None}], "matched"),
        (
            {"custom_fields": [{"id": 1, "value": ["b", "a"]}]},
            [{"id": 1, "value": ["a", "b"]}],
            "matched",
        ),
        (
            {"custom_fields": [{"id": 1, "value": ["a", "a"]}]},
            [{"id": 1, "value": ["a", "b"]}],
            "mismatch",
        ),
        (
            {"custom_fields": [{"id": 1, "value": "ignored"}]},
            [{"id": 1, "value": "text"}],
            "mismatch",
        ),
        ({}, [{"id": 1, "value": "text"}], "unavailable"),
        ({"custom_fields": []}, [{"id": 1, "value": None}], "unavailable"),
        ({"custom_fields": [{"id": 1}]}, [{"id": 1, "value": None}], "unavailable"),
        (
            {"custom_fields": [{"id": 2, "value": "text"}]},
            [{"id": 1, "value": "text"}],
            "unavailable",
        ),
        ({}, [], "matched"),
    ],
)
def test_custom_field_value_presence_and_multivalue_comparison(
    actual: dict[str, Any], expected: list[dict[str, Any]], outcome: str
) -> None:
    assert verify_custom_fields(actual, expected) == outcome


@pytest.mark.parametrize(
    "actual,outcome",
    [
        (
            {"attachments": [{"id": 9, "filename": "sample.txt", "description": "trimmed"}]},
            "matched",
        ),
        (
            {"attachments": [{"id": 9, "filename": "sample.txt", "description": "ignored"}]},
            "mismatch",
        ),
        ({"attachments": [{"id": 9, "filename": "sample.txt"}]}, "unavailable"),
        (
            {"attachments": [{"id": 10, "filename": "sample.txt", "description": "trimmed"}]},
            "mismatch",
        ),
        ({"attachments": []}, "mismatch"),
        ({}, "unavailable"),
    ],
)
def test_upload_identity_and_metadata_presence(actual: dict[str, Any], outcome: str) -> None:
    expected = [{"token": "9.abc", "filename": "sample.txt", "description": " trimmed "}]
    assert verify_uploads(actual, expected) == outcome


@pytest.mark.parametrize(
    "native,input_field",
    [
        ("assigned_to", "assigned_to_id"),
        ("category", "category_id"),
        ("fixed_version", "fixed_version_id"),
        ("parent", "parent_issue_id"),
    ],
)
@pytest.mark.parametrize(
    "present,value,outcome",
    [
        (False, None, "matched"),
        (False, 8, "mismatch"),
        (True, 8, "matched"),
    ],
)
def test_optional_reference_clear_and_supplied_id_are_distinct(
    native: str, input_field: str, present: bool, value: int | None, outcome: str
) -> None:
    actual = {native: {"id": 8}} if present else {}
    assert verify_creation_fields(actual, {input_field: value}) == {input_field: outcome}


@pytest.mark.parametrize(
    "actual,expected,outcome",
    [
        ({}, {"description": None}, "unavailable"),
        ({"description": None}, {"description": None}, "matched"),
        ({"watchers": [{"id": 8}, {"id": 3}]}, {"watcher_user_ids": [3, 8]}, "matched"),
        ({"watchers": []}, {"watcher_user_ids": [3]}, "mismatch"),
        ({}, {"watcher_user_ids": []}, "unavailable"),
    ],
)
def test_field_presence_and_watcher_set_verification(
    actual: dict[str, Any], expected: dict[str, Any], outcome: str
) -> None:
    assert set(verify_creation_fields(actual, expected).values()) == {outcome}


@pytest.mark.parametrize(
    "values,outcome",
    [
        (["matched", "matched"], "matched"),
        (["matched", "unavailable"], "unavailable"),
        (["mismatch", "unavailable"], "mismatch"),
    ],
)
def test_partial_verification_cannot_hide_mismatch(values: list[Any], outcome: str) -> None:
    assert aggregate_verification(values) == outcome


@pytest.mark.parametrize(
    "scenario,journal_id,notes,privacy",
    [
        ("unique", 2, "matched", "matched"),
        ("wrong_author", None, "unavailable", "unavailable"),
        ("old_id", None, "unavailable", "unavailable"),
        ("duplicate_matches", None, "unavailable", "unavailable"),
        ("unique_changed_note", 2, "mismatch", "matched"),
        ("ignored_privacy", 2, "matched", "mismatch"),
    ],
)
def test_new_note_matches_only_unambiguous_new_caller_journal(
    scenario: str, journal_id: int | None, notes: str, privacy: str
) -> None:
    journal = {"id": 2, "user": {"id": 3}, "notes": "new note", "private_notes": True}
    if scenario == "wrong_author":
        journal["user"] = {"id": 8}
    elif scenario == "old_id":
        journal["id"] = 1
    elif scenario == "unique_changed_note":
        journal["notes"] = "native changed note"
    elif scenario == "ignored_privacy":
        journal["private_notes"] = False
    journals = [journal]
    if scenario == "duplicate_matches":
        journals.append({**journal, "id": 3})
    result = IssueUpdateResult(
        outcome="accepted",
        upstream_accepted=True,
        resource_id=42,
        field_verification={"notes": "unavailable", "private_notes": "unavailable"},
    )
    verify_new_note(
        {"journals": journals},
        {1},
        3,
        IssueUpdateRequest(notes="new note", private_notes=True),
        result,
    )
    assert result.journal_id == journal_id
    assert result.field_verification == {"notes": notes, "private_notes": privacy}
