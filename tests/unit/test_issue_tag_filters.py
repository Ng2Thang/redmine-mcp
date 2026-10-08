import asyncio
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from redmine_mcp.common import ApplicationError, InvalidInputError
from redmine_mcp.common.read_budget import ReadBudgetPolicy, read_operation
from redmine_mcp.features.issues.queries import IssueSearch
from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.policy import ReadPolicy
from redmine_mcp.integrations.redmine.transport import AdmittedTransport

INVALID_TAGS = [
    None,
    [],
    "notification",
    ("notification",),
    [1],
    [True],
    [None],
    [{}],
    [""],
    [" "],
    [" notification"],
    ["notification "],
    ["a\nb"],
    ["a\x00b"],
    ["a\u200bb"],
    ["a%"],
    ["a_b"],
    ["a\\b"],
    ["a", "a"],
    ["a" * 256],
    [str(n) for n in range(21)],
]


@pytest.mark.parametrize("value", INVALID_TAGS)
def test_supplied_invalid_tags_rejected(value: Any) -> None:
    with pytest.raises(ValidationError):
        IssueSearch(tags_any=value)


@pytest.mark.parametrize(
    "value", [["notification"], ["A,B", "A|B", "日本語"], ["a" * 255], [str(n) for n in range(20)]]
)
def test_valid_names_preserved(value: list[str]) -> None:
    assert IssueSearch(tags_any=value).tags_any == value


def test_omitted_and_schema_contract() -> None:
    assert IssueSearch().tags_any is None
    schema = IssueSearch.model_json_schema()
    tags = schema["properties"]["tags_any"]
    assert tags["type"] == "array" and "anyOf" not in tags
    assert tags["minItems"] == 1 and tags["maxItems"] == 20
    assert tags["uniqueItems"] is True
    assert "tags_any" not in schema.get("required", [])


@pytest.mark.asyncio
async def test_service_always_available_and_omitted_call_compatible() -> None:
    reader = AsyncMock()
    service = IssueService(reader)
    await service.list_issues()
    assert "tags_any" not in reader.list_issues.call_args.kwargs
    await service.list_issues(tags_any=["notification", "urgent"])
    assert reader.list_issues.call_args.kwargs["tags_any"] == ["notification", "urgent"]


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [v for v in INVALID_TAGS if v is not None])
async def test_service_rejects_before_reader(value: Any) -> None:
    reader = AsyncMock()
    with pytest.raises(InvalidInputError):
        await IssueService(reader).list_issues(tags_any=value)
    reader.list_issues.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,code,requests",
    [
        ("request", "scan_budget_exceeded", 1),
        ("bytes", "scan_budget_exceeded", 1),
        ("scope", "scope_required", 1),
        ("depth", "scope_required", 0),
        ("timeout", "upstream_timeout", 1),
    ],
)
async def test_array_queries_keep_client_budgets(mode: str, code: str, requests: int) -> None:
    dispatched: list[httpx.Request] = []

    async def respond(request: httpx.Request) -> httpx.Response:
        dispatched.append(request)
        if mode == "timeout":
            raise httpx.ReadTimeout("offline")
        return httpx.Response(200, stream=httpx.ByteStream(json_body))

    json_body = b'{"issues":[],"total_count":500,"limit":1,"offset":0}'
    if mode == "request":
        json_body = b'{"issues":[],"total_count":1,"limit":1,"offset":0}'
    transport = AdmittedTransport(httpx.MockTransport(respond), asyncio.Semaphore(1), 1)
    async with httpx.AsyncClient(base_url="http://redmine.invalid/", transport=transport) as http:
        client = RedmineClient(http, "offline-redmine-key", ReadPolicy(retry_max_attempts=1))
        policy = ReadBudgetPolicy(
            max_requests=1 if mode == "request" else 30, max_bytes=1 if mode == "bytes" else 10000
        )
        with pytest.raises(ApplicationError) as error:
            async with read_operation(policy):
                await client.get_page(
                    "issues.json",
                    "issues",
                    {
                        "limit": 25,
                        "offset": 999 if mode == "depth" else 1,
                        "fields[]": ["issue_tags"],
                        "operators[issue_tags]": "=",
                        "values[issue_tags][]": ["A", "B"],
                    },
                    "Narrow scope",
                )
        assert error.value.code == code
    assert len(dispatched) == requests
    assert all(r.url.params.get_list("values[issue_tags][]") == ["A", "B"] for r in dispatched)
