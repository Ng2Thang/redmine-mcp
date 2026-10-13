"""Credential cleanup survives Inspector setup and process shutdown failures offline."""

import json
import subprocess
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

import httpx
import pytest

spec = spec_from_file_location(
    "prep027_inspector",
    Path(__file__).resolve().parents[2] / "scripts/verify-read-retries-inspector.py",
)
assert spec is not None and spec.loader is not None
inspector = module_from_spec(spec)
spec.loader.exec_module(inspector)


@pytest.mark.parametrize(
    "phase",
    [
        "partial_write",
        "chmod",
        "log_open",
        "spawn",
        "terminate",
        "wait",
        "kill",
        "kill_wait",
        "success",
    ],
)
def test_inspector_removes_credentials_on_every_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    monkeypatch.setattr(inspector, "ROOT", tmp_path)
    state = tmp_path / "e2e-state"
    monkeypatch.setattr(inspector, "STATE", state)
    monkeypatch.setattr(
        inspector, "preflight", lambda: {"users": {"a": {"key": "offline-private-key"}}}
    )
    config = state / "prep-027/inspector.json"
    original_client = httpx.Client
    original_write = Path.write_text
    original_open = Path.open

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/issues.json":
            return httpx.Response(200, json={"issues": [{"id": 7}]})
        if request.url.path == "/issues/7.json":
            return httpx.Response(200, json={"issue": {"id": 7, "project": {"id": 3}}})
        assert request.url.path == "/health"
        return httpx.Response(200)

    def client(*args: Any, **kwargs: Any) -> httpx.Client:
        return original_client(*args, **kwargs, transport=httpx.MockTransport(respond))

    def write(path: Path, data: str, **kwargs: Any) -> int:
        assert path.is_relative_to(tmp_path), "Offline Inspector must write only to temporary state"
        if phase == "partial_write" and path == config:
            original_write(path, data[:20], **kwargs)
            raise OSError(phase)
        return original_write(path, data, **kwargs)

    def open_file(path: Path, *args: Any, **kwargs: Any) -> Any:
        if phase == "log_open" and path.name == "server.log":
            assert config.exists()
            raise OSError(phase)
        return original_open(path, *args, **kwargs)

    def chmod(path: Path, mode: int) -> None:
        assert path == config and mode == 0o600 and config.exists()
        if phase == "chmod":
            raise OSError(phase)

    class Server:
        waits = 0
        terminated = False

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.terminated = True
            if phase == "terminate":
                raise OSError(phase)

        def wait(self, timeout: int) -> int:
            self.waits += 1
            if phase in ("kill", "kill_wait") and self.waits == 1:
                raise subprocess.TimeoutExpired("offline-server", timeout)
            if phase == "wait" or phase == "kill_wait" and self.waits == 2:
                raise OSError(phase)
            return 0

        def kill(self) -> None:
            if phase == "kill":
                raise OSError(phase)

    server = Server()

    def spawn(*args: Any, **kwargs: Any) -> Server:
        assert config.exists()
        if phase == "spawn":
            raise OSError(phase)
        return server

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert config.exists()
        if "tools/list" in command:
            result = {"tools": [{"name": name} for name in inspector.READ_OPERATIONS]}
        else:
            operation = command[command.index("--tool-name") + 1]
            data = {"id": 7 if operation == "get_issue" else 3}
            if operation == "list_issues":
                data = {"items": [{"project": {"id": 3}}]}
            result = {"content": [{"text": json.dumps(data)}]}
        return subprocess.CompletedProcess(command, 0, json.dumps({"result": result}), "")

    monkeypatch.setattr(inspector.httpx, "Client", client)
    monkeypatch.setattr(Path, "write_text", write)
    monkeypatch.setattr(Path, "open", open_file)
    monkeypatch.setattr(inspector.os, "chmod", chmod)
    monkeypatch.setattr(inspector.subprocess, "Popen", spawn)
    monkeypatch.setattr(inspector.subprocess, "run", run)
    if phase == "success":
        inspector.main()
        assert server.terminated and server.waits == 1
        assert (config.parent / "evidence.json").exists()
    else:
        with pytest.raises(OSError, match=phase):
            inspector.main()
    assert not config.exists()
