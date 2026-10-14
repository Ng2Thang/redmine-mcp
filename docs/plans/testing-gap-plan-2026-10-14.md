# Test coverage review and generation plan

Date: 2026-10-14. Status: source review and G01..G05 complete within their defined scopes;
P2 items G06/G08 deferred by the user; G07 remains separately pending at P0.

## Assessment and scope

The repository has broad functional coverage, but it does not yet establish sufficient
current acceptance for all supported behavior. Every registered operation has an explicit
offline case and an authored native lifecycle scenario. The main gaps are scenario depth,
independent expectations, infrastructure failure paths, and evidence after recent changes.
Generating another basic success case for each tool is not the first priority.

This review inspected first-party runtime code, test configuration and assertions, shared
fixtures, setup helpers, and the existing task/evidence records. It did not run pytest,
collection, coverage measurement, static-check tools, Docker, Inspector, or live calls.
No test or runtime code was changed. Counts below come from source-file enumeration,
not pytest collection; parameterization produces additional executable cases.

| Layer | Existing test modules | Assessment |
| --- | ---: | --- |
| Unit | 24 | Strong validation, read budgets/retries, membership and time-write cases; gaps in older writer branches and DEBUG logging |
| Offline integration | 24 | Broad REST/MCP authentication, schemas, mapping, gates and receipts; some assertions and fake responses need stronger independent expectations |
| E2E | 10 | All 36 tools represented, plus selected native policy/fault cases; current setup and several role/plugin/policy combinations lack matching execution evidence |

The catalog is 18 reads and 18 writes. See the existing
[operation inventory](../testing/mcp-catalog-cases.md) for per-tool owners and
[coverage matrix](testing-coverage.md) for historical evidence. This review supplements them;
it does not replace a waiver or convert an unexecuted case into a pass.

## Findings

These findings describe the initial source review. The dated G01..G03 follow-ups below
supersede their addressed offline gaps while preserving the remaining native scope.

| ID | Priority | Source evidence | Gap and consequence |
| --- | --- | --- | --- |
| F01 | P0 | [Latest testcase handoff](../testing/mcp-catalog-cases.md#execution-handoff-and-remaining-limits), [writer admission change](writer-admission-simplification.md#verification-handoff) | New cases, creation fixes and writer admission changes have no current complete passing evidence. Historical totals cannot establish the current checkout's behavior. This is primarily an execution gap. |
| F02 | P0 | [E2E configuration](../../tools/testing/e2e_config.py), [environment guards/reset](../../tools/testing/e2e_environment.py), [pytest preparation](../../tests/e2e/conftest.py), [PREP-029](tasks/prep-029-reuse-versioned-compose-e2e.md) | Tests consume setup helpers, but the unit/integration suite has no dedicated profile/preparation/reset regression modules. Wrong targets, failed seed, foreign consumers and reset path refusals need explicit offline cases. The old-layout live result does not accept the current layout. |
| F03 | P1 | [Relation fake](../../tests/integration/conftest.py), [relation adapter](../../src/redmine_mcp/integrations/redmine/issue_relations.py) | The fake imports production `expected_relation` to construct its response. A normalization bug can affect both expected and actual behavior. No dedicated independent normalization test was found. |
| F04 | P1 | [Shared writer matrix](../../tests/integration/test_current_tools.py), [writer unit cases](../../tests/unit/test_write_contracts.py), [attachment adapters](../../src/redmine_mcp/integrations/redmine/attachment_updates.py) | Existing attachment success cases use project containers. Issue/version membership proofs and wrong-container denials need dedicated cases. Older issue/note/relation/watcher writes have substantially less dedicated branch coverage than time writes and memberships. |
| F05 | P1 | [Logging implementation](../../src/redmine_mcp/observability.py), [INFO correlation cases](../../tests/integration/test_runtime_foundation.py), [logging handoff](debug-logging.md#verification-handoff) | INFO correlation/sanitization exists; dedicated DEBUG call IDs, vendor record filtering, bounded stack metadata and repeated configuration are absent from the inspected tests. Sensitive DEBUG output and concurrent context restoration remain unverified. |
| F06 | P1 | [Live tag cases](../../tests/e2e/test_issue_tag_filters.py), [historical limits](../testing/evidence/current-catalog-acceptance.md#historical-criterion-reconciliation-and-shared-policies) | Tag union currently combines a known tag with an unknown tag. This does not establish union/deduplication for two populated overlapping tags or private-role boundaries. Prerequisite skips do not establish compatibility. Broader native permission variants remain open. |
| F07 | P2 | [Catalog safety assertions](../../tests/integration/test_catalog_safety.py) | Generic invalid-input cases assert REST 422 or MCP `isError`, zero writes and selected unchanged state. They do not prove validation-specific MCP failure or absence of resource GETs. An unrelated failure could satisfy a weak assertion. Dedicated stricter tests elsewhere should be reused. |
| F08 | P2 | [Pytest configuration](../../pyproject.toml), [check script](../../scripts/check.sh), [testing roadmap](../testing-roadmap.md#baseline-history-and-further-work) | No configured coverage measurement/threshold or testing CI was found. `check.sh` performs static checks only. Wheel/image, seed and backup/restore acceptance remain separate operational gaps. This does not imply those features are broken. |

P0 addresses confidence in the current baseline and setup boundaries. P1 adds meaningful
functional depth. P2 improves diagnostics and broader release assurance.

## Ordered work packages

### G01: Establish the current baseline (P0; execution, not test generation)

Dependency: execution authorization, satisfied by the user's subsequent explicit G01
assignment. Use the existing locked dependencies.

- Run unit and integration suites separately; retain the failing node IDs and sanitized
  tracebacks. Focus first on the six reported creation failures and admission changes.
- Correct failures according to public contracts, then rerun affected cases. Record a full
  offline regression result after the final correction, distinguishing it from focused runs.
- Preserve the existing catalog inventory and time-entry tests. Do not regenerate suites
  simply because their latest passing evidence is missing.

Acceptance: evidence identifies the source revision and relevant local changes, commands,
results and unresolved failures. Existing historical counts remain dated.

Execution follow-up (2026-10-14): **complete** under the user's explicit G01 assignment.
The complete suites passed separately: 855 unit and 1,541 integration cases, totaling
2,396 passes with no failures or skips. Both commands exited 0; each reported the existing
Pydantic deprecation warning. The earlier creation regressions and current writer admission
cases passed. No runtime/test correction or rerun was needed. See the
[dated evidence](../testing/evidence/g01-offline-baseline-2026-10-14.md).
This resolves F01's offline execution gap. At that stage G02..G08 remained pending;
the subsequent G02 follow-up below records its offline completion.

### G02: Cover E2E configuration and lifecycle helpers (P0; new offline tests)

Proposed files: `tests/unit/test_e2e_config.py`,
`tests/unit/test_e2e_environment.py`, `tests/integration/test_e2e_preparation.py`,
and, where shared launcher behavior requires it, `tests/unit/test_local_env.py`.
Extend PREP-029 TEST-001..009 rather than create a competing setup contract.

| Case | Scenario | Required assertion |
| --- | --- | --- |
| SET-01 | Built-in 6.0.1 and 7.0.2 selection; complete custom 6.x profile | Exact project, URL, state path, Compose files and image pin; no fallback to another release |
| SET-02 | Unsupported/floating version, malformed/out-of-range port, partial custom settings, escaped repository path, mismatching image/version | Clear refusal before Docker mutation or fixture creation |
| SET-03 | Missing/foreign labels, wrong service/mount/port, wrong native version, malformed ownership manifest, foreign volume consumer | No seed/reset; no stop/remove command for foreign resources |
| SET-04 | Valid repeated preparation, startup failure, seed failure, incomplete setup or colliding unowned fixtures | Preparation order is explicit; valid data reused; failure aborts before test mutation; diagnostics remain private |
| SET-05 | Explicit selected reset; symlink/junction/outside state path; failing removal | Only inspected selected containers/database/files/state can be removed; other-version state and retained seed/backups survive; failures stop later actions |
| SET-06 | Default offline run, E2E without opt-in, collection-only, no selected E2E cases, selected opted-in cases | No preparation in the first four situations; exactly once for selected opted-in cases; preparation failure prevents case execution |

Use temporary roots/files and mocked subprocess/Docker/native responses. Configuration is
resolved at import time, so isolate module imports and environment state per case. Substitute
destructive functions even in refusal tests. Pytest subprocess cases belong in the future
authorized test stage; none were invoked during this review.

Acceptance: all refusal cases prove zero destructive calls; orchestration failures prove
that later seed/test steps were not reached. No real Docker or Redmine dependency offline.

Execution follow-up (2026-10-14): **complete within offline scope** under the user's G02
assignment. Added 171 passing cases (142 unit, 29 integration) in the four proposed modules
and a shared sandbox helper. The final focused run passed all 171; an earlier broader run
passed 1,095 cases including all current unit and selected startup/offline regressions.
Scoped Ruff checks passed. Initial harness errors were corrected; no setup/runtime change
was required. [Dated evidence](../testing/evidence/g02-offline-setup-2026-10-14.md) maps
SET-01..06 to PREP-029 and records exact commands and limits. Python setup/reset/gate coverage
in F02 is addressed; actual native seed/reset/coexistence acceptance remains G07/PREP-029 work.

### G03: Strengthen older writer coverage (P1; new unit/integration tests)

Proposed files: `tests/unit/test_issue_write_verification.py`,
`tests/unit/test_issue_relation_normalization.py`,
`tests/integration/test_attachment_write_boundaries.py`,
`tests/integration/test_issue_write_variants.py`,
`tests/integration/test_issue_notes.py`, `tests/integration/test_issue_relations.py`,
and `tests/integration/test_issue_watchers.py`. Keep the shared writer matrix.

| Case | Scenario | Required assertion |
| --- | --- | --- |
| WRT-01 | Every supported relation direction, inverse type, symmetric endpoint ordering, precedes/follows delay default and signed values | Literal expected endpoints/type/delay derived independently from pinned native behavior; exact outgoing payload; production helpers do not construct fake responses |
| WRT-02 | Relation deletion with duplicate/malformed/wrong-endpoint relations, one inaccessible endpoint, and differing post-delete observations | No dispatch without valid endpoint proofs; both post-delete observations preserved; matched/mismatch/unavailable remains truthful |
| WRT-03 | Attachment update/delete for project, version and issue; wrong container/version/project; missing or malformed containing list | Correct proof endpoint and exact payload; zero writes for failed proofs; accepted receipt survives unavailable/mismatching read-back |
| WRT-04 | Note belongs to another issue, invisible/missing/duplicate journal, empty-note deletion semantics, private flag omitted versus explicit value | Target membership proven before write; correct omission/null rules; vanished or unreadable journal never becomes a false matched result |
| WRT-05 | Watcher already present/absent, another target user, duplicate/malformed watchers, omitted versus empty expansion | Exact target principal; accepted no-op distinct from observed membership; omitted list is unavailable and empty list proves absence |
| WRT-06 | Issue creation/update/copy with optional references, custom-field scalar/list/null values, uploads, watcher IDs and caller-relative assignment | Field-level expected results are independently authored; correct matched/mismatch/unavailable aggregation and exact omission/clearing payloads |
| WRT-07 | Older writer post-commit malformed/missing creation ID, lost reply, failed read-back and ignored fields | Accepted versus uncertain outcomes, identifiers and verification remain accurate; exactly one mutation and no automatic replay |

Use both REST and MCP for distinct public request/error contracts; pure normalization helper
cases need unit tests only. Reuse existing transport/5xx tests instead of multiplying every
already-covered failure across all new combinations. At review the fake watcher hardcoded
user 3; the G03 implementation below extends it so another-principal tests are meaningful.

Acceptance: each case asserts dispatch count, relevant request shape and independent state or
receipt expectations. A wrong normalization, wrong container or wrong watcher ID must be
detectable by the authored assertions.

Execution follow-up (2026-10-14): **complete within offline scope** under the user's G03
assignment. Added 318 cases (66 unit, 252 integration) and replaced the fake's
production-derived relation normalization with literal native fixtures. The shared fake now handles actual watcher
targets and preserves attachment/watcher controls. After targeted corrections passed 102
cases, the final single offline run passed **2,885 cases** (1,063 unit, 1,822 integration),
including all 318 G03 additions, with no failures or skips and exit 0. Scoped Ruff checks
passed. [Dated evidence](../testing/evidence/g03-older-writers-2026-10-14.md) maps WRT-01..07,
source expectations, fixture corrections and the Pydantic/JUnit warning limits. F03 and the
selected offline F04 variants are addressed. No runtime change or native acceptance is claimed.

### G04: Cover DEBUG diagnostics (P1; new unit/integration tests)

Proposed files: `tests/unit/test_observability.py` and
`tests/integration/test_debug_logging.py`. Reuse existing INFO tests.

- LOG-01: INFO/DEBUG transitions and repeated configuration produce the intended events
  without duplicate handlers/filters. Restore global logger configuration in fixture teardown.
- LOG-02: interleaved tools and discovery receive different call IDs while internal work
  inherits the correct HTTP/call correlation. Failure and cancellation restore both contexts.
- LOG-03: sentinel keys, cookies, raw URLs/arguments/bodies, filenames and exception values
  stay out of formatted application and vendor WARNING/ERROR output, including `exc_info`.
- LOG-04: unknown endpoints/operations use placeholders; stack output contains at most 20
  code locations, excludes source/locals, and performs no stack inspection at INFO.
- LOG-05: enabling DEBUG leaves request counts, retry decisions, write receipts, stream
  closure and permit release unchanged for selected success/failure/cancellation scenarios.

G04 execution: **54 new cases** and **199 passing related regression cases**, no failures
or skips. See [dated evidence](../testing/evidence/g04-debug-logging-2026-10-14.md).
LOG-01..05 are accepted within the offline scope; no runtime change was required.

Acceptance: inspect the configured console formatter/filter path as well as captured
records; caplog alone can bypass a handler's filtering. No new live fixture is required.

### G05: Add focused native variants (P1; new E2E cases)

Dependencies: G02 acceptance, G03 where adapter expectations change, and explicit live
execution authorization. Reuse existing owned role/project fixtures and cleanup ledgers.

- NAT-01: extend tag acceptance with A-only, B-only and A+B issues; include a private issue,
  parent/child projects and an ordinary restricted caller. Assert union without duplicate IDs,
  paging/counts, scope and same-caller native/REST/MCP parity on both built-in versions.
- NAT-02: extend time creation/update policy cases for required comments, future dates,
  closed issues, explicit/default/disabled activities and minute rounding. Run changed global
  settings only in a separately isolated disposable stack; existing current-setting tests do
  not establish alternative-setting behavior.
- NAT-03: verify issue/version attachment containers, inverse/cross-project relations,
  own-versus-other journal permissions and watcher view-versus-mutation grants. Verify
  resulting native state and unchanged control resources, including accepted no-op/ignored fields.
- NAT-04: extend ordinary-user identity acceptance for locked/deleted accounts and key
  revocation. Keep rotated-key/session isolation tests already present; never substitute an
  administrator result for an ordinary-user permission case.

Define exact expected outcomes from the selected pinned Redmine/plugin contract before
generating these variants. Extend owned tag seed/cleanup explicitly if new fixtures are needed;
do not alter unrelated issues or install plugins in a test. A missing plugin prerequisite
stays an explicitly unaccepted capability, even when a skip is appropriate for a general run.

Acceptance: record exact version, plugin/settings prerequisites, caller role, selected node
IDs, native state and owned cleanup. Preserve H1..H5 scope limits until matching cases pass.

G05 execution: final selected runs passed **40 cases on each of 6.0.1 and 7.0.2**, no
failures or skips. Fourteen offline cleanup refusal cases and 14 Inspector socket calls
per version passed. See [dated evidence](../testing/evidence/g05-native-variants-2026-10-14.md).
NAT-01..04 are accepted within the selected scope; broader G07 remains separate.

### G06: Strengthen catalog safety assertions (P2; extend existing tests)

Status: deferred by the user's G04/G05 assignment; do not start P2 work now.

Owner: `tests/integration/test_catalog_safety.py`, using existing dedicated error helpers.

- CAT-06: invalid arguments produce the validation-specific MCP error contract, rather
  than any `isError`; compare with the corresponding REST validation behavior.
- CAT-07: locally invalid requests do not issue resource reads or writes. Snapshot traffic
  after MCP connection/discovery and account separately for allowed identity/capability GETs.
- CAT-08: capture relevant files, attachment metadata and versions as well as issue/time/member
  state when asserting no side effects. Retain the zero-write assertion.

Acceptance: an unrelated authorization/upstream failure cannot satisfy a validation case.
Avoid counting SDK schema-refresh discovery reads as extra business read-back requests;
the latest creation regression already documents this distinction.

### G07: Refresh current native and transport evidence (P0 after G02; execution)

Run existing live suites sequentially on the current 6.0.1 and 7.0.2 profiles. Verify
fresh/repeated preparation, coexistence and owned cleanup, then run applicable new variants.
An explicit reset/recovery scenario is a separate deliberate operation, never a normal pytest
side effect. Include current startup/Inspector and supplemental authenticated attachment-byte
checks: in-process ASGI plus native HTTP does not establish the deployed socket/container path.

Acceptance: per-version results identify failures/skips, exact setup/revision, supplemental
transport checks and cleanup. The earlier 50-case old-layout run remains historical.

### G08: Plan operational assurance and coverage measurement (P2; separate follow-up)

Status: deferred by the user's G04/G05 assignment; do not start P2 work now.

After the functional baseline is usable, plan offline seed rerun/interruption and
backup/restore refusal cases, then owned fresh-volume recovery with attachment checksums,
IDs/history/permissions and incompatible/incomplete snapshots. Add isolated wheel and
non-root image startup checks if deployment acceptance is required.

Coverage tooling is not currently configured. Propose its dependency and lockfile changes
separately, measure runtime branch coverage during an authorized offline run, and use uncovered
branches to refine this backlog. Choose any threshold after measuring; do not invent a
percentage from file counts. Testing CI and a live version matrix remain separate decisions.

## Execution handoff

The original review assignment produced the plan only. The subsequent G01 assignment ran
the first two commands below successfully from Git Bash. The native commands remain for a
separately authorized execution stage:

```bash
uv run --frozen pytest tests/unit -q
uv run --frozen pytest tests/integration -q
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e -q
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e --run-e2e -q
```

G01..G05 are complete within their defined scopes. G06/G08 remain deferred by the user's
instruction to skip P2 work. G07 is still P0 and separately pending for full native-suite,
setup/reset and broader transport acceptance; it was not included in the G04/G05 assignment.
No additional packages are required for the completed G02..G05 work.

For each package, record authored versus executed cases, focused versus full results,
skipped prerequisites, environment and cleanup independently in the existing coverage matrix
and task records. Current baseline plus passing P0/P1 cases would support the defined local
functional scope; production load, arbitrary plugins and unselected versions remain outside it.
