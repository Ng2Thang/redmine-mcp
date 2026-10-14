"""G05 NAT-01/03/04: owned native variants on each selected pinned Redmine version."""

import asyncio
import json
from typing import Any

import httpx
import pytest
import pytest_asyncio

from tests.e2e.g05_helpers import VariantEnvironment, fixture_command
from tests.helpers import mcp_session
from tests.issue_write_helpers import invoke
from tools.testing.e2e_config import STATE

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def variants(live_manifest: Any) -> Any:
    data = await asyncio.to_thread(fixture_command, "setup")
    try:
        yield VariantEnvironment(data)
    finally:
        cleanup = await asyncio.to_thread(fixture_command, "cleanup")
        assert cleanup["cleanup"] == "passed"


async def native_tags(env: Any, tags: list[str], **scope: Any) -> Any:
    fields = ["issue_tags", "status_id"]
    subprojects = scope.pop("subproject_id", None)
    if subprojects == "!*":
        fields.append("subproject_id")
        scope.update({"operators[subproject_id]": "!*", "values[subproject_id][]": [""]})
    return await env.redmine(
        "GET",
        "issues.json",
        user="reader",
        params={
            "set_filter": 1,
            "fields[]": fields,
            "operators[issue_tags]": "=",
            "values[issue_tags][]": tags,
            "operators[status_id]": "*",
            "values[status_id][]": [""],
            "sort": "id:asc",
            "limit": 100,
            **scope,
        },
    )


async def test_tag_union_dedup_private_visibility_paging_and_parent_scope(variants: Any) -> None:
    env, data = variants, variants.data
    a = await native_tags(env, [data["tags"][0]])
    b = await native_tags(env, [data["tags"][1]])
    a_ids, b_ids = ({r["id"] for r in row["issues"]} for row in (a, b))
    ids = sorted(a_ids | b_ids)
    assert a_ids & b_ids == {data["issues"]["ab"], data["issues"]["child"]}
    assert set(ids) == a_ids | b_ids == {data["issues"][name] for name in ("a", "b", "ab", "child")}
    assert a["total_count"] == len(a_ids) and b["total_count"] == len(b_ids)
    async with env.application(writer=False) as app:
        async with mcp_session(app, env.key("reader")) as session:
            for limit, offset in [(100, 0), *((1, n) for n in range(len(ids) + 1))]:
                result = await session.call_tool(
                    "list_issues",
                    {
                        "tags_any": data["tags"],
                        "status_id": "*",
                        "limit": limit,
                        "offset": offset,
                    },
                )
                assert not result.isError
                page = json.loads(result.content[0].text)
                assert page["total"] == len(ids)
                assert [r["id"] for r in page["items"]] == ids[offset : offset + limit]
            for include in (False, True):
                native_ids = set()
                for tag in data["tags"]:
                    native = await native_tags(
                        env,
                        [tag],
                        project_id=data["projects"]["parent"],
                        subproject_id="*" if include else "!*",
                    )
                    native_ids.update(r["id"] for r in native["issues"])
                scoped = await session.call_tool(
                    "list_issues",
                    {
                        "tags_any": data["tags"],
                        "status_id": "*",
                        "project_id": data["projects"]["parent"],
                        "include_subprojects": include,
                        "limit": 100,
                    },
                )
                assert not scoped.isError
                observed = json.loads(scoped.content[0].text)
                assert {r["id"] for r in observed["items"]} == native_ids
                assert (data["issues"]["child"] in {r["id"] for r in observed["items"]}) is include
    async with env.client(user="reader", writer=False) as client:
        rest = await client.get(
            "/api/v1/issues", params={"tags_any": data["tags"], "status_id": "*"}
        )
    assert rest.status_code == 200 and rest.json()["total"] == len(ids)
    assert [r["id"] for r in rest.json()["items"]] == ids
    assert data["issues"]["private"] not in ids and data["issues"]["other"] not in ids


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("cross_project", [False, True])
@pytest.mark.parametrize(
    "relation_type,canonical",
    [
        ("duplicated", "duplicates"),
        ("blocked", "blocks"),
        ("follows", "precedes"),
        ("copied_from", "copied_to"),
    ],
)
async def test_inverse_cross_project_relations_and_unchanged_control(
    variants: Any, boundary: str, relation_type: str, canonical: str, cross_project: bool
) -> None:
    env, data = variants, variants.data
    source, target, control = (
        data["issues"][n] for n in ("a", "other" if cross_project else "b", "ab")
    )
    before = await env.redmine("GET", f"issues/{control}.json", params={"include": "relations"})
    async with env.application() as app:
        status, receipt = await invoke(
            app,
            boundary,
            "create_issue_relation",
            {
                "issue_id": source,
                "issue_to_id": target,
                "relation_type": relation_type,
            },
            key=env.key("writer"),
        )
        if cross_project and not data["policies"]["cross_project"]:
            assert status == 422
            await env.redmine(
                "POST",
                f"issues/{source}/relations.json",
                user="writer",
                expected=422,
                json={"relation": {"issue_to_id": target, "relation_type": relation_type}},
            )
            assert (
                await env.redmine("GET", f"issues/{control}.json", params={"include": "relations"})
                == before
            )
            return
        assert status == 200 and receipt["outcome"] == "accepted"
        assert receipt["verification"] == "matched"
        relation_id = receipt["resource_id"]
        try:
            native = (await env.redmine("GET", f"relations/{relation_id}.json", user="writer"))[
                "relation"
            ]
            assert (native["issue_id"], native["issue_to_id"], native["relation_type"]) == (
                target,
                source,
                canonical,
            )
            if canonical == "precedes":
                assert native["delay"] == 0
        finally:
            await env.redmine("DELETE", f"relations/{relation_id}.json", expected=204)
    after = await env.redmine("GET", f"issues/{control}.json", params={"include": "relations"})
    assert after == before


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_own_note_grant_cannot_edit_other_author_note(variants: Any, boundary: str) -> None:
    env, data = variants, variants.data
    issue = data["issues"]["a"]
    before = (await env.redmine("GET", f"issues/{issue}.json", params={"include": "journals"}))[
        "issue"
    ]
    control = next(r for r in before["journals"] if r["id"] == data["journals"]["writer"])
    async with env.application() as app:
        status, own = await invoke(
            app,
            boundary,
            "update_issue_note",
            {
                "issue_id": issue,
                "journal_id": data["journals"]["own"],
                "notes": f"G05 {boundary} own edit",
            },
            key=env.key("own"),
        )
        assert status == 200 and own["outcome"] == "accepted" and own["verification"] == "matched"
        status, ignored = await invoke(
            app,
            boundary,
            "update_issue_note",
            {"issue_id": issue, "journal_id": data["journals"]["own"], "private_notes": True},
            key=env.key("own"),
        )
        # Native safe attributes ignore privacy without Set notes private permission.
        assert status == 200 and ignored["outcome"] == "accepted"
        assert ignored["verification"] == "mismatch"
        assert ignored["field_verification"] == {"private_notes": "mismatch"}
        denied, _ = await invoke(
            app,
            boundary,
            "update_issue_note",
            {
                "issue_id": issue,
                "journal_id": data["journals"]["writer"],
                "notes": "must remain unchanged",
            },
            key=env.key("own"),
        )
        assert denied in (403, 422)
    after = (await env.redmine("GET", f"issues/{issue}.json", params={"include": "journals"}))[
        "issue"
    ]
    assert next(r for r in after["journals"] if r["id"] == control["id"]) == control


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
async def test_watcher_view_and_mutation_grants_and_duplicate_noop(
    variants: Any, boundary: str
) -> None:
    env, data = variants, variants.data
    issue, target = data["issues"]["b"], data["users"]["reader"]["id"]
    before = (await env.redmine("GET", f"issues/{issue}.json", params={"include": "watchers"}))[
        "issue"
    ]
    controls = {r["id"] for r in before["watchers"]}
    assert target not in controls
    async with env.application() as app:
        denied, _ = await invoke(
            app,
            boundary,
            "add_issue_watcher",
            {"issue_id": issue, "user_id": target},
            key=env.key("watch_view"),
        )
        assert denied in (403, 422)
        try:
            for _ in range(2):
                status, receipt = await invoke(
                    app,
                    boundary,
                    "add_issue_watcher",
                    {"issue_id": issue, "user_id": target},
                    key=env.key("watch_mutate"),
                )
                assert status == 200 and receipt["outcome"] == "accepted"
                # No view grant: acceptance must survive unavailable watcher read-back.
                assert receipt["verification"] == "unavailable"
            native = (
                await env.redmine("GET", f"issues/{issue}.json", params={"include": "watchers"})
            )["issue"]
            assert [r["id"] for r in native["watchers"]].count(target) == 1
            assert {r["id"] for r in native["watchers"]} == controls | {target}
        finally:
            await env.redmine("DELETE", f"issues/{issue}/watchers/{target}.json", expected=204)
    after = (await env.redmine("GET", f"issues/{issue}.json", params={"include": "watchers"}))[
        "issue"
    ]
    assert {r["id"] for r in after["watchers"]} == controls


@pytest.mark.parametrize("boundary", ["rest", "mcp"])
@pytest.mark.parametrize("container", ["issue", "version"])
async def test_issue_and_version_attachment_mutations_preserve_controls(
    variants: Any, boundary: str, container: str
) -> None:
    env, data = variants, variants.data
    pair = (await asyncio.to_thread(fixture_command, "attachments"))[container]
    container_id = data["issues"]["a"] if container == "issue" else data["version_id"]
    before = await env.redmine("GET", f"attachments/{pair['control']}.json")
    context = {"container_type": container, "container_id": container_id}
    async with env.application() as app:
        status, update = await invoke(
            app,
            boundary,
            "update_attachment",
            {
                "attachment_id": pair["target"],
                **context,
                "description": "G05 changed",
            },
            key=env.key("writer"),
        )
        assert (
            status == 200
            and update["outcome"] == "accepted"
            and update["verification"] == "matched"
        )
        native = (await env.redmine("GET", f"attachments/{pair['target']}.json"))["attachment"]
        assert native["description"] == "G05 changed"
        status, delete = await invoke(
            app,
            boundary,
            "delete_attachment",
            {"attachment_id": pair["target"], **context},
            key=env.key("writer"),
        )
        assert (
            status == 200
            and delete["outcome"] == "accepted"
            and delete["verification"] == "matched"
        )
    await env.redmine("GET", f"attachments/{pair['target']}.json", expected=404)
    assert await env.redmine("GET", f"attachments/{pair['control']}.json") == before


@pytest.mark.parametrize(
    "action,user", [("lock", "locked"), ("delete", "deleted"), ("rotate", "rotated")]
)
async def test_ordinary_identity_revocation_in_existing_mcp_session(
    variants: Any, action: str, user: str
) -> None:
    env = variants
    action_applied = False
    async with env.application(writer=False) as app:
        try:
            async with mcp_session(app, env.key(user)) as session:
                before = await session.call_tool("get_current_user", {})
                assert not before.isError
                assert json.loads(before.content[0].text)["id"] == env.data["users"][user]["id"]
                result = await asyncio.to_thread(fixture_command, action)
                action_applied = True
                revoked = await session.call_tool("get_current_user", {})
                assert revoked.isError
        except (ExceptionGroup, httpx.HTTPStatusError) as error:
            pending = [error]
            while pending:
                leaf = pending.pop()
                if isinstance(leaf, BaseExceptionGroup):
                    pending.extend(leaf.exceptions)
                else:
                    assert action_applied and isinstance(leaf, httpx.HTTPStatusError)
                    assert leaf.response.status_code == 401
        if action == "rotate":
            async with mcp_session(app, result["key"]) as fresh:
                restored = await fresh.call_tool("get_current_user", {})
                assert not restored.isError
    await env.redmine("GET", "users/current.json", user=user, expected=401)
    (STATE / f"g05-{action}-accepted.json").write_text(
        json.dumps({"ordinary": True, "existing_session_rejected": True}), encoding="utf-8"
    )
