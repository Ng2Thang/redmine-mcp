# Code-quality audit — 2026-10-15

Scope update: the user subsequently limited quality workflows to `src/redmine_mcp/`.
The results below retain the earlier runtime/support audit and its exact evidence. Current
commands exclude support/documentation code; exclusion does not mean those findings were fixed.

## Outcome

The static audit completed with findings, exit 1, and no failed or skipped scans. Existing
convention and typing checks are not clean. Architecture checks passed. No known advisory
was returned for the 44 active Windows/Python 3.13 runtime dependencies at scan time.
The only runtime Bandit finding is an intentional empty SDK token placeholder, not a
hardcoded credential. No exploitable security defect is established by this review.

Audit tooling and reports are implemented. Runtime remediation remains in the
[prioritized backlog](../plans/code-quality-remediation.md). No runtime code was changed,
and no functional acceptance or release decision is claimed.

## Evidence

- Reference revision: `62a1ff42eb7adcf0a0f22b5bf5a9813c60a01f30`.
- Evidence directory: `.local/code-quality/20261015T032525.824074Z/`.
- Scan started: 2026-10-15 03:25:25 UTC, 10:25:25 Asia/Bangkok.
- Source hashes remained unchanged during all 16 recorded steps. The worktree includes
  uncommitted audit tooling/configuration; the reference revision alone does not identify it.
- Versions: Python 3.13.3, uv 0.12.21, Ruff 0.16.9, mypy 2.3.1, Radon 6.0.1,
  Bandit 1.9.4 and pip-audit 2.10.1.
- Raw JSON/text, exact commands, worktree paths, source hashes and exit codes are retained
  in the ignored evidence directory. Reproduce using the [workflow](../code-quality.md).

An earlier run at `20261015T031816.924068Z` exposed formatter-output parsing incompatible
with Ruff's newer text display. Its exit 2 is retained as incomplete evidence. The runner
was corrected to read the formatter's file-count summary and rerun; the later directory
above is the completed audit. It is not valid to call the earlier run clean.

## Scanner results

| Check | Runtime | Support | Interpretation |
|---|---|---|---|
| Existing Ruff | 4 diagnostics | 1 diagnostic | Confirmed convention violations |
| Formatter | 3 files | 1 file | Confirmed formatting drift; overlaps Ruff locations |
| Supplemental Ruff | 41 diagnostics | 10 diagnostics | Includes the baseline; proposed standards, not 51 new defects |
| Radon complexity >10 | 49 blocks | 17 blocks | Includes functions, nested blocks and class summaries; review signals |
| Radon MI below A | 1 module | 2 modules | Module-level metrics, not defect counts |
| Bandit | 1 LOW candidate | 112 LOW candidates | Context review required; no MEDIUM/HIGH severity finding |
| Strict mypy over `src/` | 4 errors in 2 documentation modules | n/a | No runtime-package type error reported |
| Architecture over `src/` | Passed, 132 modules | n/a | Configured import boundaries and cycles only |
| Runtime dependency export | Passed | n/a | Locked requirements; excludes development/audit groups |
| pip-audit | 0 advisories across 44 dependencies | n/a | Current Python/platform and advisory-service result only |

The runtime directory contains 130 Python modules; `src/` also contains the two documentation
tool modules. Support targets contain 15 Python files including the new audit runner.
Ruff's McCabe scores and Radon's scores differ; neither score is a measured performance result.

## Reviewed findings

### CQ-01 — Documentation tooling fails the existing strict type gate

Priority: P2. Confirmed static typing issue, not a demonstrated runtime failure.

- `src/redmine_mcp_docs/tools/vendor_assets.py:24`: `response.read()` leaks `Any` from a
  function declared to return `bytes` (`no-any-return`).
- `src/redmine_mcp_docs/tools/portal.py:185`: a loop reuses `relative` as a string after
  assigning a `Path` at line 181 (`assignment`).
- `portal.py:224`: `list_directory(path: str)` narrows the inherited method's accepted
  `str | PathLike[str]` argument (`override`).
- `portal.py:239`: `send_head()` declares a wider return type than its inherited contract
  (`override`).

Fix typing at the actual boundaries and use distinct variables. Do not disable strict mypy,
add blanket ignores or assert a type without checking the external value. Acceptance: the
existing `mypy src` command reports no errors while preserving portal/export behavior.

### CQ-02 — Existing convention and formatter drift

Priority: P3. Confirmed baseline violations.

| Location | Finding |
|---|---|
| `src/redmine_mcp/api/dependencies.py:1` | I001 import ordering |
| `src/redmine_mcp/features/attachments/router.py:1` | I001 import ordering |
| `src/redmine_mcp/integrations/redmine/retry.py:3` | I001 import ordering |
| `src/redmine_mcp/features/users/capability_service.py:168` | E501 and formatter drift |
| `src/redmine_mcp/api/body_limits.py:61` | Formatter drift |
| `src/redmine_mcp/mcp/compatibility.py:150` | Formatter drift |
| `scripts/local_env.py:84` | E501 and formatter drift |

Make a focused convention patch and inspect the diff for semantic changes. Acceptance:
existing scoped Ruff/format commands pass; no operation IDs or public contracts change.

### CQ-03 — Capability discovery combines several responsibilities

Priority: P2 maintainability candidate. Source review confirms mixed responsibilities;
no permission or pagination defect is established.

`src/redmine_mcp/features/users/capability_service.py:213` has Radon complexity 45 and Ruff
McCabe complexity 21. `_list_capabilities` combines role merging, permission evidence,
read/write tool selection, global tools, result filtering, pagination and reason stripping.

Extract cohesive helpers for role evidence and tool assembly while preserving ordering,
unknown/partial states, inherited-role merging, global tools and filtered pagination.
Do not refactor permission decisions merely to lower a score. Any behavior change requires
separately authorized verification.

### CQ-04 — Mutation transport and issue writers need focused refactoring review

Priority: P2 maintainability candidate. These paths handle mutation uncertainty, so review
them before applying broad cleanup.

| Location | Radon score |
|---|---|
| `src/redmine_mcp/integrations/redmine/write.py:96` (`_write`) | 28 |
| `src/redmine_mcp/integrations/redmine/issue_creations.py:131` (`create_issue`) | 26 |
| `src/redmine_mcp/integrations/redmine/issue_updates.py:91` (`update_issue`) | 22 |

`_write` contains dispatch, status mapping, bounded streaming, payload decoding, cleanup,
uncertainty classification and outcome logging. Source review shows a single send attempt,
redirects disabled, a deadline, response-size checks and cleanup in `finally`. Preserve those
safeguards when separating responsibilities. Additional issue mapping/validation review is
required before changing the other two methods; scan scores alone do not justify edits.

### CQ-05 — A verification helper creates a process inside an async function

Priority: P2 tooling candidate, not a production-service defect.

`scripts/verify-g05-inspector.py:49` uses `subprocess.Popen` directly inside `async def verify`
(ASYNC220). Startup can block the event loop. No timing measurement or helper execution was
performed. Review async subprocess creation or an explicit thread boundary while preserving
Windows hidden-process behavior, cleanup, log handles and cancellation semantics.

### CQ-06 — Supplemental style and metric candidates require selective adoption

Priority: P3, except risk-sensitive complexity work tracked above.

Runtime supplemental diagnostics comprise 15 C901, 10 RUF022, 6 C420, 5 SIM102, 3 I001,
1 E501 and 1 N818. Support diagnostics comprise 6 C901, RUF021, RUF005, E501 and ASYNC220.
Do not sum these with baseline diagnostics. C420 changes require checking that repeated
values are immutable; RUF005 is marked unsafe by Ruff. Renaming `RedmineWriteRejected`
for N818 requires reviewing imports and exception consumers.

MI review signals: runtime `features/issues/write_models.py` is B (15.71), support
`tools/seed/generate.py` is B (16.70), and the new `scripts/code_quality_audit.py` is B.
The new runner has no supplemental Ruff diagnostic, and all its function
complexities are <=10. Its module-size metric remains visible; no waiver or suppression
has been added. Avoid splitting files solely to improve MI.

## Security triage and exceptions

### SEC-01 — B106 empty SDK token: contextual false positive

`src/redmine_mcp/api/security.py:78` supplies `token=""` when constructing the SDK's
authenticated-user object. The preceding code has already obtained an authenticated
`AuthContext`; the subject is a SHA-256 key digest. The comment explicitly avoids storing
the raw Redmine key in this object. The empty literal is not a usable password.

Disposition: contextual false positive for hardcoded credentials. Keep the scanner finding
visible without a blanket B106 suppression. Re-review if the SDK token becomes an incoming
authentication credential or the authentication/session-binding contract changes. This is
source review, not new authentication or session acceptance evidence.

### SEC-02 — Support-process and assertion candidates

All 112 support findings are LOW severity: 76 B101 assertions, 23 B603 subprocess calls,
10 B404 subprocess imports and 3 B607 partial executable paths. Many are in verification
helpers; the new audit runner also contributes subprocess import/call candidates.

Disposition: grouped review candidates, not 112 confirmed vulnerabilities. Assertions in
verification helpers depend on Python optimization remaining disabled. Subprocess imports
and argv-based calls alone do not demonstrate injection. Review each executable source,
argument construction, PATH trust and intended trust boundary before accepting an exception.
Full per-call security triage remains in the backlog; no global skip list was introduced.

## Source review observations and limitations

Selected source review covered capability assembly, authentication/write-operation gates,
MCP registration, lifecycle ownership, write transport, retry policy and the reported typing
locations. The default catalog selection is read-only, writer selection is explicit, and
authentication precedes the SDK token placeholder. Lifecycle cleanup is registered with
`AsyncExitStack`. These are source observations, not runtime validation.

This audit does not exhaustively review all 36 operations, prove duplication absence, validate
business behavior, measure throughput or assess every logging path. No dedicated duplication
scanner, secret scanner, Ruby/Bash/JS analyzer or container vulnerability scan ran. Vendored
browser dependencies and other lockfile platforms are outside pip-audit coverage. Supplemental
Ruff findings have been grouped; not every suggested rewrite is approved.

Development prerequisites passed. The new audit runner passed its baseline Ruff, formatter,
explicit strict mypy and Bash syntax checks. No unit/integration/E2E test, startup, Docker
operation, browser check or Inspector call ran. Existing test evidence, waivers and release
limitations remain unchanged. Only static scan execution is authorized by this assignment.
