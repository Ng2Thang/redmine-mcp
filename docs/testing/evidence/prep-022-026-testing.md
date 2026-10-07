# Preparation regression testing

The user explicitly authorized test implementation and execution for prep-022 through
prep-026 on 2026-10-07. This record supersedes the earlier coding-only testing handoffs.
It covers offline regression tests, the owned pinned Redmine 7.0.2 environment, application
startup/shutdown, and Inspector 2.8.0. Deployment, CI and recovery remain outside this assignment.

## Coverage

| Task / scenarios | Executable evidence |
|---|---|
| SCHEMA-022-001/002 | `tests/integration/test_prep_contract_regressions.py`: integer, `me`, null and nullable version fields through the actual SDK; existing time-entry integration cases cover both user branches |
| SCHEMA-022-003 | `tests/unit/test_mcp_schema_parity.py`: canonical constraints, authored types, recursive local references, literal examples and atomic rejection |
| SCHEMA-022-004..006 | Compatibility cache-copy tests plus existing session isolation, allowed_all, input rejection, writer receipt and permission suites |
| SCHEMA-022-007 | `tests/e2e/test_prep_acceptance.py` and `scripts/verify-catalog-inspector.py`: caller assignment/null clearing with native comparison and owned cleanup |
| BATCH-023-001 | `tests/integration/test_membership_batch_budgets.py`: each action at 1/2/10 items through REST and SDK, one mutation per item, physical request counts |
| BATCH-023-002..004 | Existing membership fault cases migrated to dedicated settings/deadline; invalid final target, changed permissions/targets, low request/read-byte caps, accepted failed read-back and uncertain server errors |
| BATCH-023-005 | `tests/unit/test_membership_batch_policy.py`: defaults, invalid settings, concurrent reader/batch budgets and cancellation reset; integration reader cap independence |
| BATCH-023-006 | Ten-item ordinary-manager SDK add/update/delete across disposable projects; native role state checked after each action; existing catalog cases cover inherited/managed roles and assignment effects |
| BODY-024-001/002 | `tests/unit/test_request_body_limits.py`: declared/streamed oversize, zero downstream dispatch, missing/duplicate/understated/negative/huge length headers, exact cap, arbitrary chunks and early stop |
| BODY-024-003 | REST/SDK decoded N-1/N/N+1 with a small custom binary cap, and a default 5 MiB SDK upload |
| BODY-024-004/005 | Replay once, identity/unsupported encodings, partial disconnect, cancellation, GET/session DELETE bypass, derived/custom/invalid caps, pre-authentication rejection and correlation headers; existing session/writer validation regressions |
| BODY-024-006 | Owned SDK and Inspector upload attached to a disposable issue, oversized localhost MCP HTTP rejection and teardown |
| FIELD-025-001..003 | `tests/unit/test_strict_upstream_fields.py`: root/nested/inventory IDs, strict flags/file counters/progress, signed delays, future positive project status, dates/hours/null/defaults/unknown fields |
| FIELD-025-004 | REST/SDK update/copy malformed preflight sends zero writes; malformed accepted read-back keeps acceptance and one dispatch |
| FIELD-025-005/006 | Full reader/writer/session/catalog regression suites and owned native/Inspector parity |
| SDK-026-001/002 | Source boundary review and `tests/unit/test_mcp_compatibility.py`: pinned-version and registration/transport shape faults fail with sanitized startup errors |
| SDK-026-003/004 | Actual pinned SDK across schema, cache/discovery/session suites; JSON membership DELETE and fresh budgets; all existing writer 5xx/timeout receipt scenarios |
| SDK-026-005 | Real manager startup/shutdown, duplicate start, delayed readiness, context-entry failure, external cancellation and cancellation before the manager coroutine starts; existing lifecycle client cleanup |
| SDK-026-006 | Owned live application lifecycle, reader/writer gates, membership mutations, native parity and Inspector shutdown |

## Defects exposed and corrected

1. MCP SDK 1.30.0 defaults to a 4 MiB HTTP body limit. A base64-encoded 5 MiB upload,
   permitted by the application, reproduced HTTP 413. The compatibility facade now passes
   the application's effective request-body cap to the SDK manager and checks that constructor
   option. The outer ASGI admission remains before authentication and parsing.
2. Redmine 7.0.2 `Issue#safe_attributes=` deletes `assigned_to_id` and tests its value for
   truthiness. JSON null is ignored. Creation/copy and update gateways now translate an
   explicitly supplied null assignment to the native empty string while retaining null for
   expected-field verification. Omitted fields stay omitted; IDs and `me` stay unchanged.
   Native assignment tests reproduce the failure before this correction and verify clearing
   afterward. `tests/integration/test_issue_null_assignment.py` protects both REST and MCP.
3. Six baseline tests needed migration: membership fault cases used reader budget settings
   and the former 90-second deadline; lifecycle cases patched the former SDK import location
   and supplied incomplete adapters. They now use the dedicated batch policy and checked
   compatibility boundary with actual server/transport objects.

## Owned fixture handling

Live preflight checks container/image, Compose project, volume ownership/version labels and
the private manifest. Tests use ordinary caller keys for tool mutations. Administrative native
calls only create disposable fixtures and clean owned resources. Ten-item batch projects use a
unique prefix; teardown verifies ownership before deletion and native absence afterward.

Uploads are attached to disposable issues before cleanup. An unattached upload cannot be
deleted using the normal native attachment route. `tools/testing/e2e_prep_cleanup.rb` handles
interrupted preparation artifacts only: exact test filenames, no container, the owned caller,
and the marked/version-pinned environment. No shared fixture grants or environment reset occur.
API keys, upload tokens, Inspector config and raw run logs remain in ignored `.local/`.

## Reproduction

Run from the repository root in Git Bash after dependencies are installed:

```bash
uv run --no-sync pytest -q
bash scripts/check.sh
uv run --no-sync python scripts/prepare-e2e.py
uv run --no-sync pytest -q tests/e2e --run-e2e
```

The live suite invokes the pinned Inspector harness and checks native outputs. It shuts down
its localhost application and cleans disposable projects, roles, issues and attachments.

## Execution results

The final owned live suite passed **23 tests in 246.84 seconds**, including Inspector 2.8.0,
native assignment/null clearing, uploads, ten-item membership add/update/delete and cleanup.
Ten-item physical request measurements were **75 REST / 85 MCP** for add and update,
and **74 REST / 84 MCP** for delete. These totals include admission/discovery outside the
batch context; all mutations executed once per item under the dedicated 300-request cap.

The final full offline suite passed **1395 tests in 724.39 seconds**, with zero
failures or skips. All five preparation tasks are accepted for the tested functional scope.
Ruff lint/format (273 Python files), mypy (123 runtime files), architecture checks and
`git diff --check` passed. One existing Pydantic dependency deprecation warning remains. The initial 1086-case baseline exposed six obsolete fixture
assumptions (1080 passed); targeted regressions then exposed the two runtime defects above.
Neither failing run is acceptance evidence. Final Ruff, mypy, architecture and diff checks
after the runtime corrections passed as recorded above.

These functional scenarios do not establish a production load benchmark or a measured memory
ceiling under arbitrary ASGI servers. The byte-admission tests verify rejection/early stop and
dispatch boundaries; code review confirms oversized chunks are rejected before accumulation.
Coverage thresholds, CI, broad historical permission matrices and production readiness remain
deferred as documented in the current catalog ledger.


Final evidence: `.local/prep-final-offline.xml`, `.local/prep-offline-accepted.log`,
`.local/prep-live-final.log` and owned Inspector/fixture cleanup records under
`.local/testing-e2e/prep-020/`. These ignored artifacts contain private runtime evidence
and must not be committed. The final offline suite includes 309 additional cases
relative to the 1086-case baseline; two live cases were added to the former 21-case suite.
