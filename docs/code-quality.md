# Static code-quality audit

Use these workflows for convention, typing, maintainability, architecture and security review.
The audit preserves source; the fix workflow defaults to guarded formatting, with import
ordering and offline test/build verification as explicit options. Tests/build run only with
`--verify`. Neither workflow starts application services, uses Inspector or installs hooks.

## Choose a workflow

| Goal | Command | Source changes | Output |
|---|---|---|---|
| Check with terminal diagnostics | `bash scripts/fix-quality.sh --check-only` | None | Terminal |
| Apply guarded formatting and recheck | `bash scripts/fix-quality.sh` | Formatting only | Terminal |
| Additionally fix import ordering | `bash scripts/fix-quality.sh --fix-imports` | I001 fixes and formatting | Terminal |
| Format, run offline tests and build | `bash scripts/fix-quality.sh --verify` | Formatting; build artifacts | Terminal |
| Collect expanded audit evidence | `bash scripts/audit-code-quality.sh` | None | Local Markdown/JSON/text evidence |

For individual CLI commands, see [Quality Check](quality-check.md).

## Safe fixes with terminal output

Run from the repository root in Git Bash:

```bash
bash scripts/fix-quality.sh
```

The script synchronizes the locked development/audit environment, applies formatting to
`src/redmine_mcp/`, `scripts/` and `tools/seed/`, then rechecks convention, format,
strict typing, architecture, complexity, Bandit candidates and runtime dependency advisories.
mypy and the architecture checker retain their full `src/` scope. Diagnostics and the final
summary appear in the terminal; this script does not generate Markdown reports.

Use these options to check without source edits or to omit the network advisory query:

```bash
bash scripts/fix-quality.sh --check-only
bash scripts/fix-quality.sh --offline
bash scripts/fix-quality.sh --check-only --offline
```

`--check-only` can still update the local dependency environment, caches and requirements input.
`--offline` disables uv network access and skips pip-audit; the result is incomplete (exit 2).
Missing cached dependencies can prevent setup. Existing worktree edits are preserved and may
be reformatted, so review the combined diff after applying fixes.

Automatic changes default to formatting. The guard compares Python syntax-tree hashes before
and after formatting, including type comments and ignoring source positions. A mismatch returns
exit 2, preserves the source diff for review and skips optional tests/build; no rollback occurs.
Use `--fix-imports` to additionally apply only I001 import-ordering fixes with unsafe fixes
disabled. Import edits precede the snapshot and need review for initialization side effects.
General unused-import removal and syntax-modernization fixes are not applied.

To opt in to offline unit/integration tests and a package build after formatting:

```bash
bash scripts/fix-quality.sh --verify
bash scripts/fix-quality.sh --fix-imports --verify
```

These checks are independent of scanner findings; both are attempted unless the formatting
guard failed. A failed test/build makes the command exit 2. Build artifacts go into
`.local/code-quality/build/`. Tests/build do not run without `--verify`. This does not install
the wheel, launch Uvicorn/containers or invoke live E2E. A real deployment smoke check remains
separate; the offline suite uses mocked Redmine and in-process REST/MCP.

Typing, architecture, complexity and security findings require source review; there is no
guarantee that all checks
become clean. The script does not apply unsafe fixes, insert suppressions, weaken rules or
upgrade dependencies. Exit 0 means no remaining command diagnostics, exit 1 requires review,
and exit 2 means failed/skipped checks. A check's nonzero result may represent an execution
problem as well as a finding; inspect its diagnostics. Radon candidates also require review.

See [automatic fixes and rechecks](quality-check.md#automatic-fixes-and-rechecks) for the detailed
behavior and validation limits. The expanded audit below additionally collects supplemental
Ruff diagnostics and maintainability metrics; its scope is broader than the terminal pipeline.

## Audit with saved evidence

```bash
bash scripts/doctor.sh
uv sync --frozen --group audit
bash scripts/audit-code-quality.sh
```

The separate `audit` dependency group contains Bandit, Radon and pip-audit. Ruff and mypy use
the existing development group. Exact versions and transitive dependencies are committed in
`uv.lock`; runtime deployments do not need the audit group. Avoid unrelated dependency upgrades.
The wrapper resolves the repository root, so it can also be invoked by path from another directory.
Frozen uv commands may install missing locked packages; they do not update the lockfile.

To omit the network advisory query after dependencies have been installed:

```bash
UV_OFFLINE=1 bash scripts/audit-code-quality.sh --offline
```

This deliberately produces an incomplete audit with exit 2, rather than reporting dependencies
as secure. The normal run sends runtime package names and versions to pip-audit's default public
advisory service. It does not send application source or Redmine credentials. A request timeout
is 15 seconds; each scanner has a five-minute process timeout. Network failures are errors.

## Scope and policy

| Layer | Baseline | Additional review |
|---|---|---|
| Runtime: `src/redmine_mcp/` | Existing Ruff rules and formatter | Supplemental Ruff, Radon CC/MI, Bandit |
| Support: `scripts/`, `tools/seed/` | Existing Ruff rules and formatter | Supplemental Ruff, Radon CC/MI, Bandit |
| All Python under `src/` | Existing strict mypy and architecture checker | Manual boundary and contract review |
| Runtime dependencies | Active Python/platform requirements exported from `uv.lock` | pip-audit advisories |

The baseline keeps `E`, `F`, `I`, `UP`, Python 3.13, a 100-character line limit and strict mypy.
The supplemental Ruff pass extends it with `ASYNC,B,C4,C90,N,PERF,PIE,RET,RUF,SIM`, using a
McCabe complexity threshold of 10. It is an advisory profile, not a change to the existing
`scripts/check.sh` gate. Baseline and supplemental diagnostics overlap and must be deduplicated
by file, position and rule. Do not enable all rules without reviewing their applicability.

Radon complexity above 10 and maintainability index below rank A identify review candidates.
They are not proof of defects, measured performance problems or mandatory refactoring targets.
Bandit severity/confidence also require context review; do not suppress a finding merely to
obtain a clean scan. No baseline suppressions or security waivers are added by this workflow.

Only Python is scanned in the runtime/support directories. Ruby seeding, Bash helpers,
JavaScript, documentation code and vendored assets need separate review. Tests, virtual
environments, `.local/`, build output and generated state are outside scanner targets.
`mypy src` retains its established wider source scope. The architecture checker detects its
configured import boundaries and cycles; a pass does not prove every router/port/gateway
interaction or permission decision is correct.

Dependency export excludes the project itself, development dependencies and audit dependencies.
pip-audit uses pinned requirements with dependency resolution disabled. Coverage is limited to
requirements applicable to the current Python and platform, not every lockfile platform or
container environment. Unsupported/skipped packages make the dependency audit incomplete.

## Evidence and exit codes

Each invocation creates a new UTC timestamped directory under ignored `.local/code-quality/`:

- `report.md`: scanner summary, counts, limits and links to raw evidence.
- `manifest.json`: exact commands, versions, timestamps, platform, Git revision/worktree,
  source SHA-256 hashes, exit codes and duration per scanner.
- `*.stdout.txt`, `*.stderr.txt`: scanner output and execution diagnostics.
- `bandit-*.json`, `pip-audit.json`: structured security results when produced.
- `runtime-requirements.txt`: the exact dependency input exported from the lockfile.

Ruff and Radon JSON is stored in their stdout files. Raw findings can contain source excerpts;
keep them local until reviewed and sanitized. Never copy `.env`, keys, snapshots or dumps into
reports. A commit ID alone does not identify uncommitted edits; use the source hashes as well.

| Exit | Meaning |
|---|---|
| 0 | All selected scans completed with no findings or metric review signals |
| 1 | Scans completed with findings or review signals requiring triage |
| 2 | A scan failed, timed out, was skipped, or produced inconsistent evidence |

Every independent scan is attempted even when another fails. Dependency scanning depends on a
successful requirements export. Scanner errors, missing/malformed results and incomplete file
analysis are not interpreted as zero findings. Exit 1 is expected for an initial audit; it is
not a reviewed severity verdict or a production release decision.

## Review and remediation

Review candidates against their actual call paths before recording confirmed findings:

1. Deduplicate scanner output and distinguish baseline violations from proposed standards.
2. Inspect the affected source and relevant callers. Record file/line, evidence, impact,
   severity/confidence, remediation and acceptance criteria.
3. Review architecture, permission gates, MCP registration, async client ownership, timeouts,
   exception mapping, logging and repeated logic in the highest-risk areas.
4. Prioritize confirmed security/correctness defects, architecture/typing violations,
   maintainability improvements, then cosmetic convention changes. Keep false positives and
   accepted exceptions visible with a reason and review condition.
5. Make focused changes and rerun the affected static analyzers. Runtime behavior changes
   require a separately authorized test/manual-verification handoff.

The reviewed [audit record](reports/code-quality-audit.md) and
[remediation backlog](plans/code-quality-remediation.md) are English, sanitized documents.
They describe dated evidence, not future scan results. Keep historical acceptance evidence and
release limitations intact. Functional tests, coverage measurement, startup, Inspector and live
Redmine calls are outside this assignment.

## Tool references

- [Ruff configuration and output formats](https://docs.astral.sh/ruff/configuration/)
- [mypy command line](https://mypy.readthedocs.io/en/stable/command_line.html)
- [Radon command line and metric ranks](https://radon.readthedocs.io/en/latest/commandline.html)
- [Bandit command line](https://bandit.readthedocs.io/en/latest/man/bandit.html)
- [pip-audit usage and security model](https://github.com/pypa/pip-audit)
- [uv dependency groups and export](https://docs.astral.sh/uv/reference/cli/)
