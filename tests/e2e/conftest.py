"""Live fixtures are guarded by image, marker, project and manifest ownership."""

import json
import subprocess
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest

from redmine_mcp.app import create_app
from redmine_mcp.auth import WRITE_OPERATIONS
from redmine_mcp.config import Settings
from tools.testing.e2e_config import ROOT, STATE, URL
from tools.testing.e2e_environment import native_state as inspect_native_state
from tools.testing.e2e_environment import preflight as inspect_preflight


@pytest.fixture(scope="session", autouse=True)
def prepare_e2e_environment(pytestconfig: pytest.Config) -> None:
    """Prepare once before any selected live test or its session fixtures run."""
    if not pytestconfig.getoption("--run-e2e"):
        raise pytest.UsageError("Live tests require: pytest tests/e2e --run-e2e")
    STATE.mkdir(parents=True, exist_ok=True)
    log_path = STATE / "pytest-prepare.log"
    with log_path.open("w", encoding="utf-8") as log:
        try:
            result = subprocess.run(
                ["uv", "run", "--frozen", "python", "scripts/prepare-e2e.py"],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        except OSError:
            pytest.exit(
                "Cannot launch E2E preparation; ensure uv is installed and available on PATH",
                returncode=1,
            )
    if result.returncode:
        pytest.exit(
            "E2E preparation failed; inspect the selected environment's private "
            "pytest-prepare.log and seed.log",
            returncode=1,
        )


def native_state() -> Any:
    try:
        return inspect_native_state()
    except ValueError as error:
        pytest.fail(str(error), pytrace=False)


def preflight() -> Any:
    try:
        return inspect_preflight()
    except ValueError as error:
        pytest.fail(str(error), pytrace=False)


@pytest.fixture(scope="session")
def live_manifest() -> Any:
    return preflight()


class LiveEnvironment:
    def __init__(self, manifest: Any) -> None:
        self.manifest = manifest
        self.created_issues = []
        self.attachments = []
        self.relations = []

    def key(self, user: Any) -> Any:
        return self.manifest["users"][user]["key"]

    async def redmine(
        self, method: Any, path: Any, *, user: Any = "admin", expected: Any = 200, **kwargs: Any
    ) -> Any:
        async with httpx.AsyncClient(
            base_url=URL + "/",
            headers={"X-Redmine-API-Key": self.key(user)},
            trust_env=False,
            timeout=30,
        ) as client:
            response = await client.request(method, path, **kwargs)
        # Never include a response body or credentials in an assertion failure.
        assert response.status_code == expected, (
            f"Redmine {method} {path}: expected {expected}, got {response.status_code}"
        )
        return response.json() if response.content else {}

    async def owned_issue(self, issue_id: Any) -> Any:
        if issue_id in {self.manifest["issues"]["archived"], self.manifest["issues"]["disabled"]}:
            return native_state()["issues"][str(issue_id)]
        data = await self.redmine("GET", f"issues/{issue_id}.json")
        assert data["issue"]["project"]["id"] in self.manifest["projects"].values()
        return data["issue"]

    @asynccontextmanager
    async def application(
        self, *, writer: Any = True, admitted: Any = None, operations: Any = None
    ) -> Any:
        settings = Settings(
            _env_file=None,
            redmine_url=URL,
            redmine_write_enabled=writer,
            redmine_writer_auth_mode="personal_key" if writer else "pinned_key",
            redmine_writer_user_ids=(
                ",".join(
                    str(user["id"])
                    for name, user in self.manifest["users"].items()
                    if name != "admin"
                )
                if admitted is None
                else str(admitted)
            ),
            redmine_writer_operations=(operations or ",".join(WRITE_OPERATIONS)) if writer else "",
        )
        app = create_app(settings)
        async with app.router.lifespan_context(app):
            yield app

    @asynccontextmanager
    async def client(
        self, *, user: Any = "a", writer: Any = True, admitted: Any = None, operations: Any = None
    ) -> Any:
        async with self.application(writer=writer, admitted=admitted, operations=operations) as app:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                headers={"X-Redmine-API-Key": self.key(user)},
            ) as client:
                yield client

    async def upload(self, client: Any) -> Any:
        response = await client.post(
            "/api/v1/uploads", json={"filename": "e2e.txt", "content_base64": "aGVsbG8="}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["outcome"] == "accepted" and data["attachment_id"] and data["token"]
        self.attachments.append(data["attachment_id"])
        return data

    async def cleanup(self) -> None:
        errors = []
        for issue_id in reversed(self.created_issues):
            try:
                await self.owned_issue(issue_id)
                await self.redmine("DELETE", f"issues/{issue_id}.json", expected=204)
            except (AssertionError, httpx.HTTPError):
                errors.append("issue cleanup failed")
        for attachment_id in self.attachments:
            async with httpx.AsyncClient(
                base_url=URL + "/",
                headers={"X-Redmine-API-Key": self.key("admin")},
                trust_env=False,
            ) as client:
                response = await client.delete(f"attachments/{attachment_id}.json")
            if response.status_code not in (204, 404):
                errors.append("attachment cleanup failed")
        evidence = {
            "owner": "prep-018",
            "issues_created": len(self.created_issues),
            "attachments_created": len(self.attachments),
            "cleanup_errors": errors,
            "persistent_effects": "Owned fixture journals may remain; no history rollback.",
        }
        (STATE / "last-cleanup.json").write_text(json.dumps(evidence, indent=2))
        assert not errors, "Owned resource cleanup failed; inspect private cleanup evidence"


@pytest.fixture
def live(live_manifest: Any) -> Any:
    return LiveEnvironment(live_manifest)
