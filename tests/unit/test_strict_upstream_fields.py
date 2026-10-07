"""FIELD-025-001..003: native values must not silently coerce."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from redmine_mcp.features.issues.models import Attachment, Issue, IssueRelation, Journal
from redmine_mcp.features.projects.models import ProjectDetail, ProjectFile, Version
from redmine_mcp.features.reference_data.models import IssuePriority, IssueStatus, Tracker
from redmine_mcp.features.time_entries.models import TimeEntry
from redmine_mcp.features.users.models import CurrentUser
from tests.helpers import ISSUE, PROJECT

REFERENCE = {"id": 3, "name": "Example"}
ATTACHMENT = {
    "id": 9,
    "filename": "example.txt",
    "filesize": 1,
    "created_on": "2026-10-07T00:00:00Z",
    "author": REFERENCE,
}
CASES = [
    (Attachment, ATTACHMENT, ("id",)),
    (Attachment, ATTACHMENT, ("author", "id")),
    (Journal, {"id": 1, "user": REFERENCE, "created_on": "2026-10-07T00:00:00Z"}, ("id",)),
    (Journal, {"id": 1, "user": REFERENCE, "created_on": "2026-10-07T00:00:00Z"}, ("user", "id")),
    (ProjectDetail, PROJECT, ("id",)),
    (ProjectDetail, PROJECT, ("status",)),
    (Version, {"id": 1, "name": "V1", "project": REFERENCE, "status": "open"}, ("project", "id")),
    (IssueStatus, {"id": 1, "name": "New", "is_closed": False}, ("id",)),
    (IssuePriority, {"id": 1, "name": "Normal", "is_default": False}, ("id",)),
    (Tracker, {"id": 1, "name": "Bug", "default_status": REFERENCE}, ("default_status", "id")),
    (
        TimeEntry,
        {"id": 1, "project": REFERENCE, "user": REFERENCE, "hours": 0.1, "spent_on": "2026-10-07"},
        ("user", "id"),
    ),
    (
        CurrentUser,
        {
            "id": 3,
            "login": "user",
            "firstname": "First",
            "lastname": "Last",
            "memberships": [{"id": 1, "project": REFERENCE, "roles": [REFERENCE]}],
        },
        ("memberships", 0, "roles", 0, "id"),
    ),
]


@pytest.mark.parametrize("model,payload,path", CASES)
@pytest.mark.parametrize("value", [True, "1", 1.0, 0, -1])
def test_resource_and_inventory_ids_are_strict(model, payload, path, value):
    assert model.model_validate(payload)
    raw = deepcopy(payload)
    parent = raw
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ValidationError):
        model.model_validate(raw)


@pytest.mark.parametrize("field", ["filesize", "downloads"])
@pytest.mark.parametrize("value", [True, "0", 0.0, -1])
def test_file_counters_do_not_coerce(field, value):
    raw = {
        **ATTACHMENT,
        "content_url": "http://redmine.invalid/file",
        "digest": "hash",
        "downloads": 0,
    }
    raw[field] = value
    with pytest.raises(ValidationError):
        ProjectFile.model_validate(raw)


@pytest.mark.parametrize("value", [True, False, "1", 1.0, 0, -1, None])
@pytest.mark.parametrize(
    "field",
    [
        "id",
        "project",
        "tracker",
        "status",
        "priority",
        "author",
        "assigned_to",
        "category",
        "fixed_version",
        "parent",
        "custom_fields",
        "watchers",
        "children",
        "allowed_statuses",
    ],
)
def test_issue_identity_is_strict(field, value):
    raw = deepcopy(ISSUE)
    if field == "id":
        raw[field] = value
    elif field in {"custom_fields", "watchers", "children", "allowed_statuses"}:
        raw[field] = [{"id": value, "name": "Example", "subject": "Child", "is_closed": False}]
    else:
        raw[field] = {"id": value, "name": "Example"}
    with pytest.raises(ValidationError):
        Issue.model_validate(raw)


@pytest.mark.parametrize("field", ["is_private", "custom_fields", "allowed_statuses", "journals"])
@pytest.mark.parametrize("value", [0, 1, "true", "false", None])
def test_native_booleans_are_strict(field, value):
    raw = deepcopy(ISSUE)
    raw[field] = (
        value
        if field == "is_private"
        else [
            {
                "id": 1,
                "name": "Example",
                "multiple": value,
                "is_closed": value,
                "private_notes": value,
                "created_on": "2026-10-07T00:00:00Z",
                "user": {"id": 3, "name": "Writer"},
            }
        ]
    )
    with pytest.raises(ValidationError):
        Issue.model_validate(raw)


@pytest.mark.parametrize("value", [True, "10", 1.0, -1, 101])
def test_progress_rejects_coercion_and_out_of_range(value):
    with pytest.raises(ValidationError):
        Issue.model_validate({**ISSUE, "done_ratio": value})


@pytest.mark.parametrize("value", [0, 100])
def test_progress_boundaries(value):
    assert Issue.model_validate({**ISSUE, "done_ratio": value}).done_ratio == value


@pytest.mark.parametrize("value", [-7, 0, 7, None])
def test_signed_relation_delay_and_future_project_status(value):
    assert (
        IssueRelation(
            id=1, issue_id=42, issue_to_id=43, relation_type="precedes", delay=value
        ).delay
        == value
    )
    assert ProjectDetail.model_validate({**PROJECT, "status": 99}).status == 99


@pytest.mark.parametrize("value", [True, "0", 0.0])
def test_relation_delay_does_not_coerce(value):
    with pytest.raises(ValidationError):
        IssueRelation(id=1, issue_id=42, issue_to_id=43, relation_type="precedes", delay=value)


def test_dates_hours_optional_visibility_and_unknown_fields_remain_compatible():
    issue = Issue.model_validate(
        {
            **ISSUE,
            "start_date": "2026-10-07",
            "estimated_hours": 2,
            "due_date": None,
            "custom_fields": [],
            "future_native_field": "ignored",
        }
    )
    assert issue.start_date.isoformat() == "2026-10-07"
    assert issue.estimated_hours == 2.0 and issue.due_date is None
    assert issue.journals == [] and issue.watchers == []
    assert "future_native_field" not in issue.model_dump()
