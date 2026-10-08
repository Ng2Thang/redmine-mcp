"""Inspector failures must still remove the private credential config."""

import importlib.util
import subprocess
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.parametrize("cleanup_timeout", [False, True])
def test_failed_startup_removes_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    cleanup_timeout: bool,
) -> None:
    source = Path(__file__).resolve().parents[2] / "scripts/verify-tag-filters-inspector.py"
    spec = importlib.util.spec_from_file_location("tag_inspector_verifier", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / ".local").mkdir()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "owned_manifest",
        lambda: {
            "credentials": {"admin_key": "offline-redmine-key"},
        },
    )

    class Process:
        terminated = False
        killed = False
        waits = 0

        def terminate(self) -> None:
            self.terminated = True

        def kill(self) -> None:
            self.killed = True

        def wait(self, timeout: int) -> None:
            self.waits += 1
            if cleanup_timeout and self.waits == 1:
                raise subprocess.TimeoutExpired("owned-offline-process", timeout)

    class Client:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def __enter__(self) -> "Client":
            return self

        def __exit__(self, *args: Any) -> None:
            pass

        def get(self, path: str) -> None:
            raise RuntimeError("offline startup failure")

    process = Process()
    monkeypatch.setattr(module.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(module.httpx, "Client", Client)
    with pytest.raises(RuntimeError, match="offline startup failure"):
        module.main()
    assert process.terminated and process.killed == cleanup_timeout
    assert not (tmp_path / ".local/tool-036-inspector-config.json").exists()
