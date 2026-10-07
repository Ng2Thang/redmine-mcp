"""BATCH-023-005: settings and concurrent budget context isolation."""

import asyncio

import pytest
from pydantic import ValidationError

from redmine_mcp.common.read_budget import (
    MEMBERSHIP_BATCH_DEFAULTS,
    ReadBudgetPolicy,
    current_budget,
    read_operation,
)
from redmine_mcp.config import Settings


def test_batch_defaults_do_not_change_reader_defaults():
    settings = Settings(_env_file=None, redmine_url="http://redmine.invalid")
    assert (
        settings.redmine_membership_batch_max_requests
        == MEMBERSHIP_BATCH_DEFAULTS.max_requests
        == 300
    )
    assert (
        settings.redmine_membership_batch_max_read_bytes
        == MEMBERSHIP_BATCH_DEFAULTS.max_bytes
        == 30 * 1024 * 1024
    )
    assert (
        settings.redmine_membership_batch_deadline_seconds
        == MEMBERSHIP_BATCH_DEFAULTS.deadline_seconds
        == 300
    )
    assert settings.redmine_read_operation_max_requests == ReadBudgetPolicy().max_requests == 30


@pytest.mark.parametrize(
    "field",
    [
        "redmine_membership_batch_max_requests",
        "redmine_membership_batch_max_read_bytes",
        "redmine_membership_batch_deadline_seconds",
    ],
)
@pytest.mark.parametrize("value", [0, -1])
def test_invalid_batch_settings(field, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, redmine_url="http://redmine.invalid", **{field: value})


@pytest.mark.asyncio
async def test_concurrent_reader_and_batch_contexts_restore_on_cancel():
    ready = asyncio.Event()
    release = asyncio.Event()
    seen = []

    async def reader():
        async with read_operation(ReadBudgetPolicy(), fresh=True):
            budget = current_budget.get()
            budget.request()
            ready.set()
            await release.wait()
            assert current_budget.get() is budget and budget.requests == 1
            seen.append(budget)
        assert current_budget.get() is None

    async def batch():
        await ready.wait()
        try:
            async with read_operation(MEMBERSHIP_BATCH_DEFAULTS, fresh=True):
                budget = current_budget.get()
                for _ in range(35):
                    budget.request()
                seen.append(budget)
                raise asyncio.CancelledError
        finally:
            assert current_budget.get() is None
            release.set()

    result = await asyncio.gather(reader(), batch(), return_exceptions=True)
    assert isinstance(result[1], asyncio.CancelledError)
    assert len(seen) == 2 and seen[0] is not seen[1]
    assert current_budget.get() is None
