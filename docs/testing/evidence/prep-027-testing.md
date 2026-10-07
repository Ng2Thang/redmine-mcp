# PREP-027 retry verification

Date: 2026-10-07. The user assigned the testing stage after implementation and static checks.
The working tree includes the PREP-027 implementation and pre-existing bug/index edits; no
commit, deployment, reset or seed operation is part of this verification.

## Scope and environment

- Offline: locked pytest/pytest-asyncio, HTTPX MockTransport and admitted transports,
  ASGI applications with lifespan, and MCP SDK sessions. Existing offline isolation rejects
  actual network dispatch and ignores production dotenv/credentials.
- Live: existing owned `redmine-mcp-e2e` Redmine 7.0.2 deployment on localhost port 3001.
  The existing preflight checks image pin, synthetic marker, Compose project, volume labels
  and private fixture manifest before access. Ordinary caller `a` is used for reads.
- Inspector: cached Inspector 2.8.0 with `--offline`, a temporary reader on localhost port
  18087, a private ignored credential configuration and owned native read parity checks.
  The reader process is stopped and its credential config is removed in `finally`.
- Transient failures and mutation uncertainty are exercised offline only. Live verification
  performs zero mutations and creates no Redmine fixtures. Existing volumes/data are preserved.

## Tests and scenario mapping

| Scenarios | Evidence files | Selected coverage |
|---|---|---|
| TEST-001/002/004 | `tests/unit/test_read_retries.py`, `tests/integration/test_read_retries.py` | All eligible statuses and exception classes; success/exhaustion; malformed JSON/models, size limits, noneligible statuses and exceptions |
| TEST-003 | Unit admitted-transport/budget tests | Each attempt charged once; short failed decoded tail charged; new buffer on retry; request/byte exhaustion stops calls |
| TEST-005/006 | Unit settings/delay tests | Defaults, disable mode, invalid settings, bootstrap/Compose forwarding; seconds/dates, repeated/malformed headers, cap and jitter bounds |
| TEST-007 | Unit cancellation/cleanup tests | Cancellation in stream/backoff/admission/closure, retained permit during shielded cleanup, EOF cleanup failure without retry, GET/parent timeout |
| TEST-008 | Unit concurrent identities and captured logs | Request-local key, excluded cookies/default authorization, safe fixed failure names and no key/exception leakage |
| TEST-009 | REST/MCP integration tests | Identity/detail/discovery recovery, final errors, malformed/forbidden single attempts, pagination probe preserved and one operation dispatch |
| TEST-010/012 | Unit writer/capability tests and integration writer/batch/ASGI tests | Single JSON/binary mutation, recovered preflight/read-back, exhausted read-back retains acceptance, cooperative cutoff stops later writes, absolute cutoff, capability timeout and internal ASGI timing |
| TEST-011 | `tests/e2e/test_read_retries.py`, `scripts/verify-read-retries-inspector.py` | Owned native issue parity through REST/MCP, reader catalog/download gate, real reader startup and Inspector discovery/three read calls |

New deterministic support lives in `tests/retry_helpers.py`. New tests observe requests,
response closure, counters and results rather than replaying whole operations. Existing
runtime retry code did not change during this testing stage.

## Execution record

All commands are run from Git Bash at the repository root using the installed environment.

| Check | Command | Result |
|---|---|---|
| Focused offline | `uv run --frozen --no-sync pytest tests/unit/test_read_retries.py tests/integration/test_read_retries.py -q --tb=short` | 103 passed, including the strengthened invalid-JSON case |
| Adapted reader contracts | `uv run --frozen --no-sync pytest tests/integration/test_reader_contracts.py -k 'reader_error_contracts or user_006_008_profile_revocation_and_errors or user_008_profile_acquisition_failure' -q --tb=short --junitxml=.local/prep027-adapted-contracts.xml` | 81 passed; 144 unrelated cases deselected |
| Complete offline | `uv run --frozen --no-sync pytest -q --tb=short --junitxml=.local/prep027-final-offline.xml` | 1,457 passed, 41 failed old single-attempt assertions; all 41 corrected and covered by the final targeted reruns below |
| Legacy foundation contracts | `uv run --frozen --no-sync pytest tests/integration/test_runtime_foundation.py -k 'foundation_003_transport_errors_no_retry or foundation_003_011_error_status_does_not_read_body' -q --tb=short --junitxml=.local/prep027-foundation-contracts.xml` | 11 passed; 52 unrelated cases deselected |
| Owned live reader | `uv run --frozen --no-sync pytest tests/e2e/test_read_retries.py --run-e2e -q --tb=short --junitxml=.local/prep027-live.xml` | 2 passed |
| Reader startup / Inspector | `uv run --frozen --no-sync python scripts/verify-read-retries-inspector.py` | Startup, exact reader discovery and 3 read calls passed; 0 mutations |
| Lint | `uv run --frozen --no-sync ruff check .` | Passed |
| Formatting | `uv run --frozen --no-sync ruff format --check .` | Passed; 284 files formatted at final static check |
| Runtime typing | `uv run --frozen --no-sync mypy src` | Passed; 124 source files |
| Architecture | `uv run --frozen --no-sync python scripts/check_architecture.py` | Passed; 124 runtime modules |
| Diff whitespace | `git diff --check` | Passed; line-ending notices only |

Private XML/logs/evidence remain ignored under `.local/`, including
`.local/testing-e2e/prep-027/evidence.json`. No keys or upstream issue contents are copied here.

## Corrections and limitations

Initial new test failures were fixture mistakes: a preloaded MockTransport response bypassed
admitted stream closure, the binary writer call lacked its keyword-only filename, the synthetic
watcher handler did not model membership after success, and the SDK internal client attribute
name was wrong. These were corrected in the new tests without weakening runtime contracts.
A missing test import was corrected before the final run. The invalid-JSON case was strengthened
to reach JSON parsing rather than accidentally exercise only the response-size limit.

The complete regression run also exposed old single-attempt assertions for 429/503/504 and
profile read timeout/connection failures in `tests/integration/test_reader_contracts.py`.
Their expected request count now includes three GET attempts, while asserting authentication
runs once and retry URLs/profile expansion parameters remain identical. The adapted tests use
deterministic retry timing; noneligible failures still expect one GET attempt. All parameterizations
of the three modified test functions are rerun separately after these assertion changes.

Six further failures in two legacy foundation functions made the same single-attempt assumption.
Those functions now explicitly select the supported attempts `1` mode because they isolate
legacy transport error mapping and unread error-body closure. Their 11 parameterizations pass.
The new PREP-027 cases independently verify default retries, final mappings, unread bodies and
response closure across every physical attempt.

The full run collected 1,498 cases before the assertion updates. It completed with 1,457 passing
and 41 failing cases; it is not recorded as a clean full-suite run. The final targeted runs passed
all 92 parameterizations of the five modified functions. XML case IDs were reconciled: every
one of the 41 full-run failures is present and passing in those final reruns. No runtime source
changed, and no failing case remains unresolved. The entire suite was not repeated after these
test-only expectation changes. An earlier redundant full run was interrupted and is not acceptance
evidence. Temporary shell wrappers were edited while a prior process was still running, causing
a shell parse error after pytest completion; completed JUnit results and final reruns establish
the pytest outcomes independently of that wrapper error.

The existing Pydantic vendor schema deprecation warning remains; it is not a retry failure.
The full run also reports 18 existing `record_property`/JUnit xunit2 compatibility warnings.
Live checks prove ordinary read compatibility and ownership/reader boundaries, while fault
recovery and writer state/uncertainty are backed by offline scenarios. No live mutation,
production fault injection, package build, recovery exercise or release-readiness claim is made.
PREP-027 acceptance is complete from the full regression run plus corrected targeted reruns,
focused retry cases, selected owned live/Inspector checks and static checks. This does not resolve
Bug-001's original malformed upstream payload, which still needs separate sanitized evidence.

## Follow-up review fix: Inspector credential cleanup

On 2026-10-07, the user assigned the P2 cleanup finding from the subsequent review.
The harness now owns credential deletion in an outer `try/finally` before invoking verification.
This covers partial configuration writes, chmod, log opening and process launch failures.
Process shutdown retains its separate cleanup block; terminate/wait/kill failures cannot bypass
the outer credential deletion. Verification errors still propagate rather than being reported
as a passing run. No runtime retry behavior changed.

`tests/unit/test_retry_inspector_cleanup.py` exercises eight failure paths plus the successful
path using temporary files, mocked HTTP and subprocesses: **9 passed**. Setup/write and
shutdown failures all leave no credential config. No native Redmine, Docker, server process
or Inspector command is launched by these tests. An initial collection error caused by importing
the hyphenated script as a Python module was corrected with explicit file-based module loading.

Commands: `uv run --frozen --no-sync pytest tests/unit/test_retry_inspector_cleanup.py -q
--tb=short --junitxml=.local/prep027-cleanup.xml`; scoped Ruff lint/format checks;
`uv run --frozen --no-sync mypy src`; `git diff --check`. All pass after the correction.
The prior full-suite/live/Inspector counts above remain historical evidence; those checks were
not repeated for this harness-only fix.
