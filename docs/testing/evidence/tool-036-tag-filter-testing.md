# TOOL-036 tag filter testing

Date: 2026-10-08. User-authorized testing of `list_issues.tags_any` after renumbering.
The task is [TOOL-036](../../plans/tasks/tool-036-filter-issues-by-tags.md).

## Scope and environment

Offline tests use fake settings without `.env`, MockTransport, in-process REST/MCP and the
existing external-network isolation. No dependencies were installed. Runtime code was unchanged
during this testing stage. Test code and an opt-in Inspector helper were added.

The user initially selected localhost:3001, then explicitly corrected the target to
**localhost:3000**. Read-only container metadata confirms the selected target is the marked
`redmine-mcp-test` synthetic environment, bound to 127.0.0.1:3000, running
**Redmine 6.0.5-bookworm**. This differs from the task's Redmine 7.0.2 target; these results
are evidence for the selected environment, not 7.0.2 acceptance. The existing Tags installation
was not changed; its installed version was not independently established through REST.

Credentials were loaded from ignored local files and never printed or committed. All live
Redmine requests were GET. No plugin installation, Ruby execution, seed/reset, fixture/tag
assignment, database access or other server modification occurred. Existing `notification`
assignments supplied the positive control; no tagged data was created for these checks.

## Results and traceability

| Evidence | Scenario | Result |
|---|---|---|
| TOOL-036-EVID-003-OFFLINE | TOOL-036-001..004 | 82 focused offline tests passed |
| TOOL-036-EVID-003-CLEANUP | Inspector helper failure recovery | 2 offline startup/cleanup-timeout cases passed; credential config removed in both |
| TOOL-036-EVID-003-LIVE | Selected TOOL-036-005 checks | 3 live tests passed on port 3000 / Redmine 6.0.5 |
| TOOL-036-EVID-003-INSPECTOR | Discovery, array schema and selected TOOL-036-005 calls | Inspector 2.8.0 discovery and two read-only calls passed |
| TOOL-036-EVID-003-STATIC | New test/helper files and runtime types | Scoped Ruff lint/format passed; mypy passed for 124 source files |
| TOOL-036-EVID-003-REGRESSION | Existing unit/integration compatibility | 1,584 offline tests passed, 1 warning, 863.78 seconds |

Offline coverage establishes exact repeated query encoding, complete core-filter translation
for all four status variants and assignee ID/me, project/subprojects, includes, UTC update time,
native page metadata and offset probes. Synthetic ANY/overlap and unknown-name results validate
the application mapping against mocked native behavior, not the real plugin's semantics.
Input cases cover omission vs explicit null, strict strings/lists, count/length bounds,
duplicates, blanks, whitespace, Unicode controls/format characters, wildcard/escape rejection,
and comma/pipe/non-ASCII preservation. REST/MCP parity, upstream auth/resource/validation errors,
malformed rows/counts, request/byte budgets, scope/depth guards and timeout mappings are covered.

Live results establish a nonempty baseline (489 issues), empty nonexistent-tag control, and
native/REST/MCP total parity for that control. Both admin and reader keys were exercised against
existing `notification` assignments. Adding a nonexistent second name preserves notification
matches (ANY), page size 1 preserves native totals/order, matching IDs are unique, and selected
exact-project results contain only that project. The tests do not reconstruct assigned tag arrays.
Inspector exercised notification plus the nonexistent name and the nonexistent name alone.

Inspector started a temporary read-only MCP listener on 127.0.0.1:18083, then stopped it.
The private Inspector credential config was removed after execution. Raw outputs and sanitized
summaries remain ignored under `.local/`; public evidence contains no credentials or issue text.

## Commands

Run from Git Bash with installed dependencies:

```bash
uv run --frozen --no-sync pytest tests/unit/test_issue_tag_filters.py tests/integration/test_issue_tag_filters.py -q -p no:cacheprovider
uv run --frozen --no-sync pytest tests/unit/test_tag_inspector_cleanup.py -q -p no:cacheprovider
uv run --frozen --no-sync pytest tests/e2e/test_issue_tag_filters.py --run-e2e -q -rs -p no:cacheprovider
uv run --frozen --no-sync python scripts/verify-tag-filters-inspector.py
uv run --frozen --no-sync pytest tests/unit tests/integration -q -p no:cacheprovider
uv run --frozen --no-sync ruff check tests/unit/test_issue_tag_filters.py tests/unit/test_tag_inspector_cleanup.py tests/integration/test_issue_tag_filters.py tests/e2e/test_issue_tag_filters.py scripts/verify-tag-filters-inspector.py
uv run --frozen --no-sync ruff format --check tests/unit/test_issue_tag_filters.py tests/unit/test_tag_inspector_cleanup.py tests/integration/test_issue_tag_filters.py tests/e2e/test_issue_tag_filters.py scripts/verify-tag-filters-inspector.py
uv run --frozen --no-sync mypy src
git diff --check
```

The live file and helper intentionally guard the user-selected existing port-3000 container,
marker, exact observed 6.0.5 image, credentials location and host-port binding. They do not
use the port-3001 fixture's Rails inspection or create fixtures. A changed target requires an
explicitly assigned metadata/fixture revision rather than silently reusing credentials.

## Corrections and remaining acceptance

Initial focused run: 77 passes. Five client budget/error cases were subsequently added; the
request-budget test initially used a total that triggered the scope guard first. Correcting
that fixture yields 82 passes. Initial test/helper lint issues were formatting/import wrapping
only and were corrected. No runtime implementation defect was found by these runs.
Two additional offline helper tests prove credential-config removal after startup failure and
after a subprocess cleanup timeout; the latter kills only the helper's owned process.
The full regression run collected the initial 77 tag cases before the five extra budget cases
and two cleanup cases were added. Those seven additions were covered by the final focused
82-case run and the separate two-case cleanup run. No runtime source changed between runs;
the full-suite count is not presented as a fresh collection of the later expanded test set.

The first port-3001 attempt stopped before API calls because its image includes the repository's
digest pin. After matching the exact pin, its negative control returned the same total 10 as
the baseline; that target did not establish native tag support. The user then selected port
3000; acceptance is not claimed for the earlier target.

TOOL-036 remains **blocked** for complete target acceptance: Redmine 7.0.2 with established
Tags 2.2.0 Light support, an existing issue assigned both of two real selected names, and
known tagged private/hidden issues with ordinary-role expected visibility are still required.
No waiver of these cases or of the target-version requirement was supplied. Use existing
permitted fixtures; do not install or mutate Redmine to satisfy them. A Pydantic deprecation
warning from installed integration dependencies occurred; it did not fail the checks.
