"""Boundary tests for operation-local budgets and stateless pagination."""

import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from redmine_mcp.common import ApplicationError
from redmine_mcp.common.pagination import PageRequest, PaginationGuard
from redmine_mcp.common.read_budget import (
    ReadBudget,
    ReadBudgetPolicy,
    charge_bytes,
    charge_request,
    current_budget,
    read_operation,
)
from redmine_mcp.config import Settings


@pytest.mark.parametrize(
    "total,limit,pages,broad",
    [(0, 25, 0, False), (250, 25, 10, False), (251, 25, 11, True), (1000000, 100, 10000, True)],
)
def test_pagination_description(total: Any, limit: Any, pages: Any, broad: Any) -> None:
    policy = PaginationGuard().describe(total, limit)
    assert (policy.total_pages, policy.requires_narrowing) == (pages, broad)


def test_non_aligned_depth_and_scope_boundary() -> None:
    guard = PaginationGuard()
    guard.check_depth(25, 225, "narrow")
    guard.require_scope(250, 25, "narrow")
    for call in (
        lambda: guard.check_depth(25, 226, "narrow"),
        lambda: guard.require_scope(251, 25, "narrow"),
    ):
        with pytest.raises(ApplicationError, match="narrow") as error:
            call()
        assert error.value.code == "scope_required"


@pytest.mark.parametrize(
    "values", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": True}, {"offset": "1"}]
)
def test_page_request_rejects_invalid_types_and_bounds(values: Any) -> None:
    with pytest.raises(ValidationError):
        PageRequest(**values)


def test_request_and_byte_budget_exact_boundary() -> None:
    budget = ReadBudget(ReadBudgetPolicy(max_requests=2, max_bytes=3))
    budget.request()
    budget.request()
    budget.consume(3)
    for call in (budget.request, lambda: budget.consume(1)):
        with pytest.raises(ApplicationError) as error:
            call()
        assert error.value.code == "scan_budget_exceeded"


def test_synchronous_deadline_boundary() -> None:
    budget = ReadBudget(ReadBudgetPolicy(deadline_seconds=2), started=10)
    with patch("redmine_mcp.common.read_budget.monotonic", return_value=12):
        with pytest.raises(ApplicationError) as error:
            budget.check_deadline()
    assert (error.value.code, error.value.status) == ("read_operation_timeout", 504)


@pytest.mark.asyncio
async def test_nested_budget_inherits_and_fresh_context_restores() -> None:
    async with read_operation(ReadBudgetPolicy(max_requests=2)):
        outer = current_budget.get()
        charge_request()
        async with read_operation(ReadBudgetPolicy(max_requests=100)):
            assert current_budget.get() is outer
            charge_request()
        async with read_operation(ReadBudgetPolicy(), fresh=True):
            assert current_budget.get() is not outer
            charge_bytes(3)
        assert current_budget.get() is outer
        with pytest.raises(ApplicationError):
            charge_request()
    assert current_budget.get() is None


@pytest.mark.asyncio
async def test_timeout_resets_budget_context() -> None:
    with pytest.raises(ApplicationError) as error:
        async with read_operation(ReadBudgetPolicy(deadline_seconds=0.01)):
            await asyncio.Event().wait()
    assert error.value.code == "read_operation_timeout"
    assert current_budget.get() is None


@pytest.mark.parametrize("public_url", [None, "", "https://public.invalid/redmine/"])
def test_settings_public_url_and_approved_defaults(public_url: Any) -> None:
    settings = Settings(
        _env_file=None, redmine_url="http://redmine.invalid", redmine_public_url=public_url
    )
    assert (
        settings.redmine_max_concurrent_requests,
        settings.redmine_admission_timeout_seconds,
        settings.redmine_read_operation_max_requests,
        settings.redmine_read_operation_deadline_seconds,
    ) == (50, 30, 30, 90)
    assert (settings.redmine_public_url is None) == (not public_url)


@pytest.mark.parametrize(
    "field,value",
    [
        ("redmine_max_concurrent_requests", 0),
        ("redmine_admission_timeout_seconds", float("inf")),
        ("redmine_read_operation_deadline_seconds", 0),
        ("redmine_public_url", "https://user:secret@public.invalid"),
    ],
)
def test_settings_reject_unsafe_limits_and_urls(field: Any, value: Any) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, redmine_url="http://redmine.invalid", **{field: value})
