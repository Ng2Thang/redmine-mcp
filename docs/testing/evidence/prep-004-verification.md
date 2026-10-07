# prep-004 verification evidence: 2026-10-02

This record extends the 2026-10-01 evidence without replacing it. The user accepted
prep-003's implementation with testing pending and requested continuation of prep-004.
The existing testing authorization was retained. The user separately authorized the focused
MCP startup fix after the concurrency test exposed a runtime defect.

## Offline and static execution

Commands ran from the repository root in Git Bash:

```bash
bash scripts/doctor.sh
uv run --frozen pytest -q --tb=short -p no:cacheprovider
bash scripts/check.sh
uv build
git diff --check
```

The final offline run passed **356 tests** in 43.32 seconds, with one existing Pydantic
deprecation warning. Ruff lint/format, mypy for 79 source files, and the architecture gate for
79 runtime modules passed. Both source and wheel distributions built. Whitespace checks passed.
No dependency or lockfile changes were needed.

New cases live in [runtime foundation tests](../../../tests/integration/test_runtime_foundation.py) and
[reader contract tests](../../../tests/integration/test_reader_contracts.py). The existing 46-case suite and
its earlier uncommitted edits were preserved. The mock fixture now supports isolated identity,
profile, and asynchronous upstream responses without loading real credentials.

| Task / scenarios | Executed coverage | Result and remaining limitation |
|---|---|---|
| prep-003: FOUNDATION-001 | Invalid/repeated/missing headers, rejected/malformed identity, explicit allow/deny policy | Pass offline |
| prep-003: FOUNDATION-002 | Concurrent keys, default authorization and cookie exclusion, redirects, relative paths, separate transport timeouts | Pass for executed cases; no real pool-load experiment |
| prep-003: FOUNDATION-003 | Pool/connect/read timeout, transport failure, status mapping, no retries or consumed error bodies | Pass offline |
| prep-003: FOUNDATION-004 | Failure before/after headers, sanitized stream exception, cancellation, context cleanup | Pass offline |
| prep-003: FOUNDATION-005 | Concurrent REST correlations, untrusted incoming IDs, inherited internal context, log secret exclusion | Pass for executed cases; complete live MCP correlation matrix remains pending |
| prep-003: FOUNDATION-006 | Strict counts/rows/page echoes, omitted echoes, empty/short pages, detail mismatch, complete collection counts | Pass offline |
| prep-003: FOUNDATION-007 | All 11 tools through SDK, two mocked identities, same-user REST/MCP visibility, lifespan closure | Pass offline; second ordinary live account unavailable |
| prep-003: FOUNDATION-008 | Service IDs, pagination, filters, timezone, cross-field rules, duplicate/invalid includes | Pass offline |
| prep-003: FOUNDATION-009 | Failed acquisition and MCP startup, cleanup failure, closed clients, repeated lifespan, hints, open-session shutdown | Pass offline |
| prep-003: FOUNDATION-010 | Concurrent normalized keys bound to their verified principals | Pass offline |
| prep-003: FOUNDATION-011 | Deadline/cancellation, exact/overflow limits, decoded gzip limit, invalid/non-object JSON, parser recursion error, stream closure | Pass offline; recursion failure is injected because accepted nesting depth differs between Python builds |
| prep-003: FOUNDATION-012 | Catalog mismatch, hidden/duplicate routes, missing schemas/auth, wrong method, flat/context representations | Pass for executed cases; no claim of exhaustive version compatibility |
| tool-002: DETAIL-001 through DETAIL-004 | Default/empty/single/all includes, nested children/journals, invalid selection, omissions, malformed expansion, ID mismatch, REST/MCP errors | Pass offline |
| tool-003: PROJECT-001 through PROJECT-003 | Optional/complete fields, list regression, invalid/mismatched ID, auth/errors, SDK discovery/invocation | Pass offline |
| tool-004: STATUS-001/002 | Populated/empty/malformed arrays, flags, exact path, auth/errors, SDK call | Pass offline |
| tool-005: TRACKER-001/002 | Populated/empty/malformed arrays, optional fields, exact path, auth/errors, SDK call | Pass offline |
| tool-006: PRIORITY-001/002 | Populated/empty/malformed arrays, default flag, exact path, auth/errors, SDK call | Pass offline |
| tool-007: VERSION-002/003; tool-008: CATEGORY-002/003 | Optional fields, empty/malformed arrays, strict complete counts, invalid IDs, auth/errors, SDK calls | Pass offline |
| tool-009: CATISSUE-001 through CATISSUE-004 | Combined category filters, nullable/malformed reference, validation, query/defaults, pagination, errors, SDK calls | Pass offline |
| tool-010: TARGETISSUE-001 through TARGETISSUE-005 | Combined version filter and each subproject choice, nullable/malformed reference, validation, query/defaults, pagination, SDK calls | Pass offline |
| tool-011: DATE-001 through DATE-003; HOURS-001 through HOURS-003 | List/detail dates and hours, nulls/zero, invalid dates, negative/string/boolean/nonfinite hours | Pass offline |
| tool-011: AGG-001/002, COMPAT-001, MCP-001 | Two pages, inclusive dates, missing/out-of-range dates, parent/child references, unique direct-hour sum, incomplete hours, prior defaults and tools | Pass offline |
| tool-012: ENTRY-001 through ENTRY-004, PAGE-001 | Two credited users and dates, zero hours, empty page, malformed/cross-issue rows, 101 entries over two populated pages | Pass offline |
| tool-012: AGG-001, AUTH-001, VIS-001, COMPAT-001, MCP-001 | Six issues, ID deduplication and decimal user totals, issue/time-entry permission failures, existing tools and SDK errors | Pass offline |
| tool-013: USER-001 through USER-009 | Caller binding, membership/role validation, inheritance, email observations, secret exclusion, revocation, acquisition failures, SDK schema/hints | Pass for executed cases; full live variants are not inferred from mock results |

Current contract corrections apply to future requirements and acceptance procedures only:
authenticate with each caller's `X-Redmine-API-Key`, use `requesting_redmine_user` visibility,
and map a rejected key to 401. Valid authentication may perform an identity lookup before
rejecting feature inputs; invalid inputs must prevent resource dispatch. Discovery snapshots
and earlier execution notes retain their historical wording.

## Runtime defect and authorized correction

The initial concurrent MCP session test intermittently returned 500 with the SDK error
`Task group is not initialized`. FastAPI-MCP 0.4 published its lazy-start flag before the
session manager entered its `run()` context. The user authorized a runtime correction.

The MCP adapter now starts an owned manager task during application lifespan startup. A
readiness future resolves when the SDK context enters; requests are accepted afterward.
Failed or cancelled startup cancels and joins the manager task. The existing exit stack
registers shutdown first and still closes both HTTP clients if MCP startup or cleanup fails.
Deterministic readiness/failure/cancellation tests, concurrent caller tests, and an actual open
MCP session at shutdown pass. Operation names, inputs, authentication, and response shapes stay
stable. FastAPI-MCP's private transport access remains isolated in the adapter for the pinned
0.4.0 integration.

## Read-only synthetic execution

The existing marker and complete manifests were checked. Docker reported the pinned
the previously observed Redmine container healthy. Inspector 2.8.0 used a temporary localhost app on
port 18080 and the existing restricted ordinary-user key. Comparisons used direct Redmine
REST under the same key. No seeding, resets, role/token changes, or Redmine writes occurred.
Private harnesses and redacted result files remain in ignored `.local/`.

| Scenarios | Observed result | Acceptance status |
|---|---|---|
| FOUNDATION-007, USER-001/010 | Inspector discovers all 11 operations. Current identity, public profile fields, ten memberships, and roles match Redmine. | Partial: only one ordinary key |
| PROJECT-004 | A visible project matches Redmine; the marked restricted project is absent from listing and its tool call fails safely. | Pass for this fixture |
| STATUS-003, TRACKER-003, PRIORITY-003 | Registry IDs/names match: six statuses, three trackers, five priorities; returned closed/default flags match. | Registry comparison passes; full project-tracker/workflow matrix remains pending |
| VERSION-001/004 | The sampled base project returns zero versions and matches Redmine. | Partial: populated sharing/private-role matrix remains pending |
| CATEGORY-001/004 | Both Redmine and Inspector reject category reading with 403 for the ordinary reader. | Permission boundary observed; populated/private content fixtures unavailable |
| DETAIL-005 | Six journal IDs and private flags match Redmine; one returned row is flagged private. Allowed statuses are empty in both responses. | Partial: no contrasting ordinary role or nonempty transition fixture |
| tool-012 LIVE-001 | A history issue returns three entries; IDs, issue IDs, credited users, hours, dates, and count match Redmine. | Same-reader comparison passes; all-user completeness remains unestablished |
| TARGETISSUE-006 | History Alpha / Sprint 02 / Bug queries return zero exact-project matches and seven descendant-inclusive matches; IDs, count, and version membership match Redmine with explicit `id:asc` sorting. | Pass for this fixture |
| tool-011 LIVE-001 | Thirteen exact Operations Bugs have matching list dates/hours; sampled detail fields match. No issue qualifies for the required September 2026 interval. | Partial: the empty qualifying set cannot validate a nonempty direct-hour aggregate |
| CATISSUE-005 | No category fixture is recorded and this reader cannot discover category IDs. | Blocked |
| USER-010 full matrix | The credential artifact contains one ordinary personal key; the other account IDs have no stored personal keys. | Blocked |

An earlier comparison harness needed UTF-8 decoding, public-field selection, explicit sort,
and handling of expected Inspector error exits. These were harness corrections, not runtime
changes. One subsequent tracker CLI invocation failed without a captured safe error code;
the earlier registry comparison passed, and the targeted version/schedule tail completed.
A complete clean live rerun is still required; partial runs are not a passing full matrix.
Temporary app processes were stopped by the harness. Graceful shutdown and open-session
cleanup are established by the offline lifespan cases, not by forcibly stopping those processes.

## Revised acceptance scope: live checks waived

On 2026-10-02 the user requested skipping live checks for prep-004. The remaining live
permission/correlation matrix, fixture acquisition, and clean Inspector rerun are **waived**.
The partial live results and limitations above remain historical evidence. They do not
establish complete live visibility or data completeness.

The passing 356-test offline suite, static checks, source/wheel builds, scenario ledger, and
authorized runtime fix satisfy the revised offline acceptance scope. prep-004 is **verifying**,
ready for user acceptance; unavailable live fixtures no longer block this task. The earlier
question about ignored fixture-file paths is superseded by the waiver. Explicit task acceptance
still precedes prep-005. Later tasks retain their own verification and dependency requirements.
