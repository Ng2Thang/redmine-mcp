"""Read-only tag controls; never install plugins or create/alter tag fixtures."""

import json
import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest

from redmine_mcp.app import create_app
from redmine_mcp.config import Settings
from tests.helpers import mcp_session

STATE = Path(__file__).resolve().parents[2] / ".local"
TARGET = "http://127.0.0.1:3000"
UNKNOWN = "mcp-tag-control-036-does-not-exist-7f93c1"


def owned_manifest() -> dict[str, Any]:
    result = subprocess.run(
        ["docker", "inspect", "redmine-mcp-test-redmine-1"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, "Owned Redmine container unavailable"
    container = json.loads(result.stdout)[0]
    config = container["Config"]
    env = dict(v.split("=", 1) for v in config["Env"] if "=" in v)
    assert config["Image"] == "redmine:6.0.5-bookworm"
    assert env.get("REDMINE_TEST_MARKER") == "redmine-mcp-synthetic-v1"
    assert config["Labels"]["com.docker.compose.project"] == "redmine-mcp-test"
    assert container["NetworkSettings"]["Ports"]["3000/tcp"] == [
        {"HostIp": "127.0.0.1", "HostPort": "3000"}
    ]
    manifest = json.loads((STATE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["kind"] == "redmine-mcp-synthetic-v1"
    manifest["credentials"] = json.loads((STATE / "credentials.json").read_text(encoding="utf-8"))
    return manifest


def create_tag_reader_app() -> Any:
    owned_manifest()
    return create_app(Settings(_env_file=None, redmine_url=TARGET))


@pytest.mark.asyncio
@pytest.mark.parametrize("identity", ["admin_key", "reader_key"])
async def test_existing_notification_any_scope_and_pagination(identity: str) -> None:
    manifest = owned_manifest()
    key = manifest["credentials"][identity]
    async with httpx.AsyncClient(
        base_url=TARGET + "/",
        headers={"X-Redmine-API-Key": key},
        trust_env=False,
        timeout=30,
    ) as native:
        selected = await native.get(
            "issues.json",
            params={
                "set_filter": 1,
                "fields[]": ["issue_tags", "status_id"],
                "operators[issue_tags]": "=",
                "values[issue_tags][]": ["notification"],
                "operators[status_id]": "*",
                "values[status_id][]": [""],
                "sort": "id:asc",
                "limit": 100,
            },
        )
    assert selected.status_code == 200
    expected = selected.json()
    assert expected["total_count"] <= 100, "Known-tag fixture exceeds this bounded check"
    if identity == "admin_key":
        assert expected["total_count"] > 0, "Known notification tag has no positive control"
    ids = [row["id"] for row in expected["issues"]]
    app = create_tag_reader_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": key},
        ) as rest:
            combined = await rest.get(
                "/api/v1/issues",
                params={
                    "tags_any": ["notification", UNKNOWN],
                    "status_id": "*",
                    "limit": 100,
                },
            )
            assert combined.status_code == 200
            assert combined.json()["total"] == expected["total_count"]
            assert [row["id"] for row in combined.json()["items"]] == ids
            assert len(ids) == len(set(ids))
            for offset, issue_id in enumerate(ids):
                page = await rest.get(
                    "/api/v1/issues",
                    params={
                        "tags_any": "notification",
                        "status_id": "*",
                        "limit": 1,
                        "offset": offset,
                    },
                )
                assert page.status_code == 200
                assert page.json()["total"] == expected["total_count"]
                assert [row["id"] for row in page.json()["items"]] == [issue_id]
            if ids:
                project_id = expected["issues"][0]["project"]["id"]
                scoped = await rest.get(
                    "/api/v1/issues",
                    params={
                        "tags_any": "notification",
                        "project_id": project_id,
                        "include_subprojects": "false",
                        "status_id": "*",
                        "limit": 100,
                    },
                )
                assert scoped.status_code == 200
                assert all(row["project"]["id"] == project_id for row in scoped.json()["items"])
                assert scoped.json()["total"] == len(scoped.json()["items"])
        async with mcp_session(app, token=key) as session:
            result = await session.call_tool(
                "list_issues",
                {
                    "tags_any": ["notification", UNKNOWN],
                    "status_id": "*",
                    "limit": 100,
                },
            )
        assert not result.isError
        assert [row["id"] for row in json.loads(result.content[0].text)["items"]] == ids


@pytest.mark.asyncio
async def test_read_only_live_negative_control_and_mcp_parity() -> None:
    manifest = owned_manifest()
    key = manifest["credentials"]["admin_key"]
    structured = {
        "set_filter": "1",
        "fields[]": ["issue_tags", "status_id"],
        "operators[issue_tags]": "=",
        "values[issue_tags][]": [UNKNOWN],
        "operators[status_id]": "*",
        "values[status_id][]": [""],
        "limit": "2",
    }
    async with httpx.AsyncClient(
        base_url=TARGET + "/",
        headers={"X-Redmine-API-Key": key},
        trust_env=False,
        timeout=30,
    ) as native:
        ordinary = await native.get("issues.json", params={"status_id": "*", "limit": 2})
        control = await native.get("issues.json", params=structured)
    assert ordinary.status_code == control.status_code == 200
    baseline, filtered = ordinary.json(), control.json()
    assert baseline["total_count"] > 0, "Existing environment has no control issues"
    app = create_app(Settings(_env_file=None, redmine_url=TARGET))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"X-Redmine-API-Key": key},
        ) as rest:
            response = await rest.get(
                "/api/v1/issues",
                params={
                    "tags_any": UNKNOWN,
                    "status_id": "*",
                    "limit": 2,
                },
            )
        assert response.status_code == 200
        async with mcp_session(app, token=key) as session:
            tools = await session.list_tools()
            assert any(t.name == "list_issues" for t in tools.tools)
            result = await session.call_tool(
                "list_issues",
                {
                    "tags_any": [UNKNOWN],
                    "status_id": "*",
                    "limit": 2,
                },
            )
        assert not result.isError
        sdk = json.loads(result.content[0].text)
    assert response.json()["total"] == sdk["total"] == filtered["total_count"]
    evidence = {
        "task": "TOOL-036",
        "target": "http://localhost:3000",
        "version": "6.0.5",
        "ownership": "redmine-mcp-test",
        "method": "GET only",
        "baseline_total": baseline["total_count"],
        "negative_control_total": filtered["total_count"],
        "rest_sdk_native_total_parity": True,
        "native_list_has_tags": any("tags" in row for row in filtered["issues"]),
        "tag_control_supported": filtered["total_count"] == 0,
        "limitations": "No plugin installation, fixture mutation, positive overlap or Inspector",
    }
    (STATE / "tool-036-tag-control.json").write_text(
        json.dumps(evidence, indent=2),
        encoding="utf-8",
    )
    if filtered["total_count"]:
        pytest.skip(
            "Native tag negative control returns issues; target does not establish tag support"
        )
