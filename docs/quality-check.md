# Quality Check

Run these commands individually from the repository root in Git Bash on Windows.
Results appear directly in the terminal. Individual check commands perform static analysis
without rewriting source. The fix workflow defaults to formatting, with import ordering as an
explicit option. Tests and package builds run only with `--verify`; no workflow starts services.

See the [code-quality workflow overview](code-quality.md#choose-a-workflow) to choose between
terminal checks, guarded formatting and the expanded audit with saved evidence.

## Setup

Install the locked development and audit dependencies:

```bash
uv sync --frozen --group audit
```

Ruff and mypy belong to the development group. Radon, Bandit and pip-audit belong to
the separate audit group. Frozen commands preserve `uv.lock`.

## Automatic fixes and rechecks

Apply formatting with a Python syntax-tree comparison, then run every check documented below:

```bash
bash scripts/fix-quality.sh
```

The script shows tool diagnostics and a final summary in the terminal. It does not
generate Markdown reports. Fix targets are `src/redmine_mcp/`, `scripts/` and `tools/seed/`;
mypy and architecture checks retain their wider `src/` scope. It synchronizes the locked
development/audit environment before starting and does not require a clean worktree.
Existing edits remain in place; review the combined source diff after running it. General lint
fixes are not applied automatically. The default command does not run tests or build packages.

To additionally fix import ordering, explicitly select `--fix-imports`:

```bash
bash scripts/fix-quality.sh --fix-imports
```

Only I001 fixes are enabled in that mutation step, with unsafe fixes disabled. Unused imports
are not removed and syntax-modernization fixes are not applied. Import ordering can affect
modules with initialization side effects, so review those edits. `--check-only` and
`--fix-imports` cannot be combined.

The formatting guard snapshots syntax-tree hashes before formatting and compares them afterward,
including type comments but excluding source positions. Import ordering runs before the snapshot
when explicitly selected. A mismatch, added/deleted file or parse failure produces exit 2 and
skips optional tests/build. Existing edits are retained for review; the script does not reset or
roll back the worktree. This conservative check can flag changed docstrings/type comments;
matching trees reduce formatting risk but do not prove all runtime behavior is correct.

To run the same pipeline without source changes, or without a network advisory query:

```bash
bash scripts/fix-quality.sh --check-only
bash scripts/fix-quality.sh --offline
bash scripts/fix-quality.sh --check-only --offline
```

`--check-only` still synchronizes dependencies and may write tool caches and the runtime
requirements input file. `--offline` disables uv network access; missing cached dependencies
can prevent setup. The skipped advisory query always makes an offline run incomplete.

| Check | Automatic action |
|---|---|
| Ruff convention/imports | Check only; optionally apply I001 ordering fixes with `--fix-imports` |
| Ruff formatting | Reformat selected Python files |
| mypy | Display typing diagnostics for source review |
| Architecture | Display import/cycle diagnostics for source review |
| Radon | Display complexity candidates for refactoring review |
| Bandit | Display security candidates for context review |
| pip-audit | Display advisories; no automatic package upgrades |

No tool can safely repair every typing, architecture, complexity or security finding without
understanding the intended behavior. This script does not use broad lint fixes, insert suppressions,
weaken checks or upgrade dependencies to make output appear clean. Dependency remediation must
update `pyproject.toml` and `uv.lock` together; pip-audit's automatic environment fixes do not
provide that repository-specific workflow.

### Optional verification after formatting

Explicitly request offline unit/integration tests and an isolated package build:

```bash
bash scripts/fix-quality.sh --verify
bash scripts/fix-quality.sh --fix-imports --verify
```

Use `--check-only --verify` to verify the current source without formatting it. Only the presence
of `--verify` enables these commands:

```bash
uv run --frozen --no-sync --group audit pytest tests/unit tests/integration
uv build --no-sources --out-dir .local/code-quality/build
```

Tests and the build are independent checks and are both attempted, even when other checks report
findings. If the formatting guard failed, both are skipped. A failed test/build returns exit 2.
The build writes artifacts under ignored `.local/` and may download build-system dependencies;
`--offline` requires these dependencies to be cached. It does not update project dependency pins.

The existing offline suite covers service/model logic, REST/MCP contracts, permission/session
isolation and in-process startup/cleanup with mocked Redmine. It does not establish installed
wheel behavior, Uvicorn/socket/container startup or real Redmine behavior. The optional build
checks packaging, but does not install or run the resulting wheel. Smoke/E2E verification stays
separate; see the [coverage gaps](plans/testing-gap-plan-2026-10-14.md#findings).

Exit 0 means configured static commands reported no remaining diagnostics. Exit 1 means a
check returned nonzero or Radon printed review candidates/diagnostics. Exit 2 means setup or
a command or optional verification failed, or checks were skipped. A nonzero checker result can
be an execution problem as well as a finding: read its output before triage. Independent checks
continue after failures;
pip-audit only runs after a successful requirements export. Final rechecks determine whether
Ruff findings remain after formatting. Static success does not establish functional acceptance.

Implementation validation included Ruff lint/format and strict mypy for the new syntax-tree guard,
Bash syntax and diff whitespace checks. The revised pipeline, import-ordering option and `--verify`
have not been executed against existing source during this assignment. Syntax-tree matching,
test/build success and actual deployment behavior must not be inferred from source review.

## Ruff: convention and imports

Check runtime code and supporting Python scripts against the existing repository rules:

```bash
uv run --frozen ruff check src/redmine_mcp scripts tools/seed
```

## Ruff: formatting

Identify files that need formatting without rewriting them:

```bash
uv run --frozen ruff format --check src/redmine_mcp scripts tools/seed
```

## mypy: strict typing

Check all Python code under `src/`, including the documentation tools:

```bash
uv run --frozen mypy src
```

## Radon: complexity

Show runtime blocks with complexity rank C or worse, including their numeric scores:

```bash
uv run --frozen --group audit radon cc src/redmine_mcp -s -n C
```

Rank C starts at complexity 11. Treat these results as review candidates, not proof of
incorrect behavior. To inspect support scripts separately:

```bash
uv run --frozen --group audit radon cc scripts tools/seed -s -n C
```

## Bandit: Python security candidates

Scan runtime Python code:

```bash
uv run --frozen --group audit bandit -r src/redmine_mcp
```

Scan support scripts separately:

```bash
uv run --frozen --group audit bandit -r scripts tools/seed
```

Review severity, confidence and the affected code before deciding whether a finding is
valid. A scanner finding is not automatically a confirmed vulnerability.

## pip-audit: runtime dependency vulnerabilities

Export the locked runtime requirements, excluding the project itself and dependency groups.
Then query advisories without resolving or installing the exported dependencies:

```bash
mkdir -p .local/code-quality

uv export --locked --no-dev --no-default-groups --no-emit-project \
  --no-hashes --no-header --no-annotate --format requirements-txt \
  --output-file .local/code-quality/runtime-requirements.txt && \
uv run --frozen --group audit pip-audit \
  --requirement .local/code-quality/runtime-requirements.txt \
  --no-deps --disable-pip --progress-spinner off --timeout 15
```

The `&&` runs pip-audit only after a successful export, preventing accidental reuse of an
older input file. The requirements file is an input artifact in ignored `.local/`;
the audit result is displayed in the terminal.

This checks packages applicable to the current Python and platform. The advisory query
requires network access and sends package names and versions to the public advisory service.
A network failure or skipped package means incomplete coverage, not a clean result.

## Repository architecture

Run the existing static import-boundary and cycle checker over `src/`:

```bash
uv run --frozen python scripts/check_architecture.py
```

## Suggested order and interpretation

1. Run Ruff convention and formatting checks.
2. Run mypy and the architecture checker.
3. Review Radon complexity candidates.
4. Review Bandit findings and dependency advisories.

Run each command separately so a nonzero result does not prevent the next check.
Nonzero exit codes can indicate findings or execution errors; read the terminal diagnostics.
Do not apply broad suppressions or automatic fixes solely to obtain a clean result.

Python scanners do not analyze Bash, Ruby or JavaScript files in the support directories.
These commands do not target `tests/`, virtual environments, generated state or vendored
browser assets. Static analysis does not establish functional acceptance.

For an interactive local report, Qodana Community for Python is a separate option.
Its inspections differ from this CLI baseline; it does not automatically replace the
repository's strict typing or custom architecture rules.

## References

- [Ruff configuration](https://docs.astral.sh/ruff/configuration/)
- [mypy command line](https://mypy.readthedocs.io/en/stable/command_line.html)
- [Radon command line](https://radon.readthedocs.io/en/latest/commandline.html)
- [Bandit command line](https://bandit.readthedocs.io/en/latest/man/bandit.html)
- [pip-audit](https://github.com/pypa/pip-audit)
- [Qodana local reports](https://www.jetbrains.com/help/qodana/configuration-reference.html)
