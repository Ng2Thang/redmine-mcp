"""Collect static audit evidence without importing or executing application code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "src/redmine_mcp"
EXTRA_RULES = "ASYNC,B,C4,C90,N,PERF,PIE,RET,RUF,SIM"
TIMEOUT_SECONDS = 300


@dataclass(frozen=True)
class Check:
    name: str
    command: list[str]
    parser: str
    report: str | None = None


@dataclass(frozen=True)
class Result:
    name: str
    command: list[str]
    status: str
    exit_code: int | None
    seconds: float
    findings: int | None
    detail: str
    stdout: str
    stderr: str
    report: str | None


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("Expected a JSON object with string keys")
    return cast(dict[str, object], value)


def records(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("Expected a JSON array")
    return [mapping(item) for item in value]


def count_detail(items: list[dict[str, object]], key: str) -> str:
    counts = Counter(str(item[key]) for item in items)
    return ", ".join(f"{name}: {count}" for name, count in counts.most_common(12)) or "No findings"


def summarize_ruff(content: str) -> tuple[int, str]:
    items = records(json.loads(content))
    if any(item.get("code") is None for item in items):
        raise ValueError("Ruff reported a syntax error; analysis is incomplete")
    return len(items), count_detail(items, "code")


def summarize_bandit(content: str) -> tuple[int, str]:
    data = mapping(json.loads(content))
    if data["errors"]:
        raise ValueError("Bandit could not analyze every selected file")
    items = records(data["results"])
    return len(items), count_detail(items, "issue_severity")


def summarize_dependencies(content: str) -> tuple[int, str]:
    dependencies = records(mapping(json.loads(content))["dependencies"])
    if any("skip_reason" in item for item in dependencies):
        raise ValueError("pip-audit skipped dependencies; analysis is incomplete")
    count = sum(len(records(item["vulns"])) for item in dependencies)
    return count, f"{len(dependencies)} active runtime dependencies; {count} advisories"


def summarize_complexity(content: str) -> tuple[int, str]:
    blocks: dict[tuple[str, str, str], int] = {}
    for filename, value in mapping(json.loads(content)).items():
        pending = records(value)
        while pending:
            block = pending.pop()
            key = filename, str(block["lineno"]), str(block["name"])
            complexity = block["complexity"]
            if not isinstance(complexity, int):
                raise ValueError("Invalid complexity value")
            blocks[key] = complexity
            pending.extend(records(block.get("methods", [])))
            pending.extend(records(block.get("closures", [])))
    hotspots = sorted(blocks.items(), key=lambda item: item[1], reverse=True)
    count = sum(score > 10 for _, score in hotspots)
    top = "; ".join(f"{file}:{line} {name}={score}" for (file, line, name), score in hotspots[:5])
    return count, f"{count} blocks above complexity 10; top: {top}"


def summarize_maintainability(content: str) -> tuple[int, str]:
    data = mapping(json.loads(content))
    count = sum(mapping(value)["rank"] != "A" for value in data.values())
    return count, f"{len(data)} modules; {count} modules below MI rank A (review signal)"


JSON_SUMMARIZERS: dict[str, Callable[[str], tuple[int, str]]] = {
    "ruff": summarize_ruff,
    "bandit": summarize_bandit,
    "dependencies": summarize_dependencies,
    "complexity": summarize_complexity,
    "maintainability": summarize_maintainability,
}


def summarize(parser: str, content: str, exit_code: int) -> tuple[int, str]:
    """Validate evidence before interpreting a tool's nonzero exit as findings."""
    if parser in {"complexity", "maintainability", "export"} and exit_code != 0:
        raise ValueError("Metrics or prerequisite command failed")
    if parser in JSON_SUMMARIZERS:
        return JSON_SUMMARIZERS[parser](content)
    if parser == "export":
        return 0, "Runtime requirements exported from uv.lock for this Python/platform"
    if parser == "format":
        summary = re.search(r"(\d+) files? would be reformatted", content)
        count = int(summary[1]) if summary else 0
        detail = f"{count} files would be reformatted"
    else:
        pattern = (
            r"^.+:\d+(?::\d+)?: error:"
            if parser == "mypy"
            else r"^(Forbidden import:|Import cycle:)"
        )
        count = len(re.findall(pattern, content, re.MULTILINE))
        detail = f"{count} diagnostics"
    if exit_code == 1 and not count:
        raise ValueError(f"{parser} failed without recognized diagnostics")
    return count, detail


def run_check(check: Check, directory: Path) -> Result:
    stdout = directory / f"{check.name}.stdout.txt"
    stderr = directory / f"{check.name}.stderr.txt"
    started = time.monotonic()
    exit_code: int | None = None
    status = "error"
    count: int | None = None
    detail = "Analysis did not complete"
    try:
        environment = {**os.environ, "PYTHONUTF8": "1", "RADONFILESENCODING": "UTF-8"}
        with (
            stdout.open("w", encoding="utf-8") as output,
            stderr.open("w", encoding="utf-8") as error,
        ):
            completed = subprocess.run(
                check.command,
                cwd=ROOT,
                env=environment,
                stdout=output,
                stderr=error,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        exit_code = completed.returncode
        if exit_code not in {0, 1}:
            raise ValueError(f"Tool execution failed (exit {exit_code})")
        content = (
            (directory / check.report).read_text(encoding="utf-8")
            if check.report
            else stdout.read_text(encoding="utf-8")
        )
        if check.parser in {"format", "mypy", "architecture"}:
            content += "\n" + stderr.read_text(encoding="utf-8")
        count, detail = summarize(check.parser, content, exit_code)
        finding_parsers = {"ruff", "bandit", "dependencies", "format", "mypy", "architecture"}
        if check.parser in finding_parsers and exit_code != int(count > 0):
            raise ValueError("Exit code and parsed findings disagree; inspect raw evidence")
        status = "findings" if count else "clean"
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        detail = f"{type(exc).__name__}: {exc}"
        count = None
    result = Result(
        check.name,
        check.command,
        status,
        exit_code,
        round(time.monotonic() - started, 3),
        count,
        detail,
        stdout.name,
        stderr.name,
        check.report,
    )
    print(f"[{status}] {check.name}: {detail}", flush=True)
    return result


def module_command(module: str, *arguments: str) -> list[str]:
    return [sys.executable, "-m", module, *arguments]


def executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"Required executable is unavailable: {name}")
    return path


def checks(directory: Path) -> list[Check]:
    return [
        Check(
            "ruff-runtime",
            module_command("ruff", "check", RUNTIME, "--no-fix", "--output-format=json"),
            "ruff",
        ),
        Check("format-runtime", module_command("ruff", "format", "--check", RUNTIME), "format"),
        Check(
            "ruff-review-runtime",
            module_command(
                "ruff",
                "check",
                RUNTIME,
                "--no-fix",
                "--extend-select",
                EXTRA_RULES,
                "--config",
                "lint.mccabe.max-complexity=10",
                "--output-format=json",
            ),
            "ruff",
        ),
        Check("complexity-runtime", module_command("radon", "cc", "--json", RUNTIME), "complexity"),
        Check(
            "maintainability-runtime",
            module_command("radon", "mi", "--json", RUNTIME),
            "maintainability",
        ),
        Check(
            "bandit-runtime",
            module_command(
                "bandit",
                "-r",
                RUNTIME,
                "-f",
                "json",
                "-o",
                str(directory / "bandit-runtime.json"),
            ),
            "bandit",
            "bandit-runtime.json",
        ),
        Check(
            "mypy",
            module_command(
                "mypy", RUNTIME, "--no-pretty", "--no-color-output", "--show-error-codes"
            ),
            "mypy",
        ),
        Check("architecture", [sys.executable, "scripts/check_architecture.py"], "architecture"),
        Check(
            "runtime-requirements",
            [
                executable("uv"),
                "export",
                "--locked",
                "--no-dev",
                "--no-default-groups",
                "--no-emit-project",
                "--no-hashes",
                "--no-header",
                "--no-annotate",
                "--format",
                "requirements-txt",
                "--output-file",
                str(directory / "runtime-requirements.txt"),
            ],
            "export",
            "runtime-requirements.txt",
        ),
    ]


def git_metadata() -> dict[str, str]:
    result: dict[str, str] = {}
    for name, arguments in (
        ("commit", ["rev-parse", "HEAD"]),
        ("worktree", ["status", "--short", "--untracked-files=normal"]),
    ):
        completed = subprocess.run(
            [executable("git"), *arguments],
            cwd=ROOT,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(f"Could not collect Git {name} metadata")
        result[name] = completed.stdout.strip()
    return result


def source_manifest() -> dict[str, str]:
    paths = {
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        Path(__file__).resolve(),
        ROOT / "scripts/audit-code-quality.sh",
        ROOT / "scripts/check_architecture.py",
    }
    paths.update((ROOT / RUNTIME).rglob("*.py"))
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", "").replace("\n", " ")


def write_report(directory: Path, results: list[Result], metadata: dict[str, object]) -> None:
    (directory / "manifest.json").write_text(
        json.dumps({**metadata, "checks": [asdict(result) for result in results]}, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Static code-quality audit",
        "",
        f"Started (UTC): {metadata['started_utc']}",
        "",
        "This report contains scanner candidates, not reviewed defects or runtime acceptance.",
        "No tests, startup, Inspector, Docker, auto-fix or source rewrite is performed.",
        "Baseline and supplemental Ruff results overlap; do not sum them as unique defects.",
        "Complexity >10 and MI below A are review signals, not production failure thresholds.",
        "",
        "| Check | Status | Count | Exit | Detail | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for result in results:
        links = f"[stdout]({result.stdout}), [stderr]({result.stderr})" if result.stdout else "n/a"
        if result.report:
            links += f", [report]({result.report})"
        count = "unknown" if result.findings is None else str(result.findings)
        code = "not available" if result.exit_code is None else str(result.exit_code)
        lines.append(
            f"| {result.name} | {result.status} | {count} | {code} | "
            f"{markdown_cell(result.detail)} | {links} |"
        )
    lines.extend(
        [
            "",
            "## Scope and reproduction",
            "",
            "All source scans target `src/redmine_mcp/` only.",
            "Support scripts, seed tools and documentation code are outside scanner scope.",
            "Tests, generated state, virtual environments and vendored assets are excluded.",
            "pip-audit checks uv.lock runtime requirements for the active Python/platform.",
            "It contacts the public advisory service using package names and versions.",
            "A skipped audit or dependency is incomplete coverage, never a clean security result.",
            "",
            "`manifest.json` records commands, versions, Git state and source SHA-256 hashes.",
            "Review raw JSON/text before assigning priority or changing code. See",
            "[audit workflow](../../../docs/code-quality.md) for triage and verification limits.",
            "",
        ]
    )
    (directory / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Skip the advisory service query")
    arguments = parser.parse_args()
    started = datetime.now(UTC)
    parent = ROOT / ".local/code-quality"
    parent.mkdir(parents=True, exist_ok=True)
    directory = parent / started.strftime("%Y%m%dT%H%M%S.%fZ")
    directory.mkdir()
    metadata: dict[str, object] = {
        "started_utc": started.isoformat(),
        "python": sys.version,
        "platform": sys.platform,
        "source_scope": RUNTIME,
        "git": git_metadata(),
        "source_sha256": source_manifest(),
        "versions": {
            name: version(name) for name in ("ruff", "mypy", "radon", "bandit", "pip-audit")
        },
        "supplemental_ruff_rules": EXTRA_RULES,
        "offline": arguments.offline,
    }
    uv_version = subprocess.run(
        [executable("uv"), "--version"],
        capture_output=True,
        encoding="utf-8",
        timeout=15,
        check=True,
    )
    metadata["uv_version"] = uv_version.stdout.strip()
    print(f"Evidence directory: {directory}", flush=True)
    results = [run_check(check, directory) for check in checks(directory)]
    audit = Check(
        "pip-audit",
        module_command(
            "pip_audit",
            "--requirement",
            str(directory / "runtime-requirements.txt"),
            "--no-deps",
            "--disable-pip",
            "--progress-spinner",
            "off",
            "--timeout",
            "15",
            "--format",
            "json",
            "--output",
            str(directory / "pip-audit.json"),
        ),
        "dependencies",
        "pip-audit.json",
    )
    if arguments.offline or results[-1].status != "clean":
        reason = (
            "Offline mode selected" if arguments.offline else "Runtime dependency export failed"
        )
        results.append(
            Result(audit.name, audit.command, "skipped", None, 0, None, reason, "", "", None)
        )
    else:
        results.append(run_check(audit, directory))
    unchanged = metadata["source_sha256"] == source_manifest()
    metadata["source_unchanged_during_scan"] = unchanged
    if not unchanged:
        results.append(
            Result(
                "source-stability",
                [],
                "error",
                None,
                0,
                None,
                "Audited source changed during scanning; rerun against a stable worktree",
                "",
                "",
                None,
            )
        )
    exit_code = (
        2
        if any(result.status in {"error", "skipped"} for result in results)
        else int(any(result.status == "findings" for result in results))
    )
    metadata["exit_code"] = exit_code
    metadata["finished_utc"] = datetime.now(UTC).isoformat()
    write_report(directory, results, metadata)
    print(f"Report: {directory / 'report.md'}", flush=True)
    return exit_code


if __name__ == "__main__":
    try:
        audit_exit_code = main()
    except (OSError, RuntimeError, PackageNotFoundError, subprocess.SubprocessError) as exc:
        print(f"Audit execution failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    raise SystemExit(audit_exit_code)
