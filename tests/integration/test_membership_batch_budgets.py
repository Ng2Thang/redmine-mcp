"""BATCH-023: physical work, batch boundaries and request-local accounting."""

import pytest

from redmine_mcp.common.read_budget import current_budget
from tests.integration.test_project_members import invoke, item
from tests.membership_helpers import membership

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("action", ["add", "update", "delete"])
@pytest.mark.parametrize("count", [1, 2, 10])
async def test_default_budget_executes_full_batch(
    writer_app, synthetic, boundary, action, count, record_property
):
    synthetic.members = {n: membership(n, user_id=n + 100) for n in range(20, 20 + count)}
    targets = range(1000, 1000 + count) if action == "add" else range(20, 20 + count)
    status, result = await invoke(
        writer_app, action, [item(action, n) for n in targets], boundary=boundary
    )
    assert status == 200 and result["phase"] == "executed", result
    assert len(result["results"]) == count
    assert all(
        r["outcome"] == "accepted" and r["verification"] == "matched" for r in result["results"]
    ), result
    assert synthetic.writes == count
    # The ordinary-reader cap was 30; ten-item batches must use the dedicated cap.
    assert len(synthetic.requests) <= 300 + 5  # SDK admission identity calls are outside batch.
    record_property("physical_native_requests", len(synthetic.requests))
    if count == 10:
        assert len(synthetic.requests) > 30
    assert current_budget.get() is None


@pytest.mark.parametrize("action", ["add", "update", "delete"])
async def test_invalid_last_target_prevents_entire_batch(writer_app, synthetic, action):
    original = synthetic.respond

    async def respond(request):
        if request.url.path == "/projects/999.json":
            import httpx

            return httpx.Response(404, json={})
        return await original(request)

    synthetic.respond = respond
    status, result = await invoke(
        writer_app, action, [item(action), item(action, 21, project_id=999)]
    )
    assert status == 200 and result["phase"] == "preflight_failed"
    assert synthetic.writes == 0
    assert current_budget.get() is None


async def test_reader_cap_does_not_override_batch_policy(application_factory, synthetic):
    async with application_factory(
        redmine_write_enabled=True,
        redmine_writer_operations="update_project_members",
        redmine_read_operation_max_requests=1,
    ) as app:
        status, result = await invoke(app, "update", [item("update")])
    assert status == 200 and result["results"][0]["outcome"] == "accepted", result
    assert synthetic.writes == 1 and current_budget.get() is None
