"""Private native fixture results and applications for owned G05 projects."""

import json
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx

from redmine_mcp.app import create_app
from redmine_mcp.auth import WRITE_OPERATIONS
from redmine_mcp.config import Settings
from tests.e2e.conftest import LiveEnvironment
from tools.testing.e2e_config import STATE, URL, native_command, process_environment


def fixture_command(action: str, *, command: Any = native_command, state: Path = STATE) -> Any:
    result = subprocess.run(
        command("g05_fixtures.rb", action),
        env=process_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    path = state / f"g05-{action}.log"
    path.write_text(result.stdout + result.stderr, encoding="utf-8")
    path.chmod(0o600)
    assert result.returncode == 0, f"Owned G05 {action} failed; inspect its private log"
    records = [line for line in result.stdout.splitlines() if line.startswith('{"')]
    assert len(records) == 1, "Expected one private G05 fixture result"
    return json.loads(records[0])


class VariantEnvironment(LiveEnvironment):
    def __init__(self, data: Any, url: str = URL) -> None:
        super().__init__(data)
        self.data = data
        self.url = url

    async def redmine(
        self, method: str, path: str, *, user: str = "admin", expected: int = 200, **kwargs: Any
    ) -> Any:
        async with httpx.AsyncClient(
            base_url=self.url + "/",
            headers={"X-Redmine-API-Key": self.key(user)},
            trust_env=False,
            timeout=30,
        ) as client:
            response = await client.request(method, path, **kwargs)
        assert response.status_code == expected, (
            f"Native {method} expected {expected}, got {response.status_code}"
        )
        return response.json() if response.content else {}

    @asynccontextmanager
    async def application(self, *, writer: bool = True, operations: str | None = None) -> Any:
        app = create_app(
            Settings(
                _env_file=None,
                redmine_url=self.url,
                redmine_write_enabled=writer,
                redmine_writer_operations=(operations or ",".join(WRITE_OPERATIONS))
                if writer
                else "",
            )
        )
        async with app.router.lifespan_context(app):
            yield app


def inspector_app() -> Any:
    """Localhost-only server factory for the explicitly invoked G05 Inspector helper."""
    from tests.e2e.conftest import preflight

    preflight()
    data = json.loads((STATE / "g05-fixtures.json").read_text(encoding="utf-8"))
    assert data["owner"] == "g05"
    return create_app(
        Settings(
            _env_file=None,
            redmine_url=URL,
            redmine_write_enabled=True,
            redmine_writer_operations=",".join(WRITE_OPERATIONS),
        )
    )
