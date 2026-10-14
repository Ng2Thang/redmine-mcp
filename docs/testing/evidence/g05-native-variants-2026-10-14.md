# G05: Focused native variants

Date: 2026-10-14. Status: complete within NAT-01..04's selected native scope.

## Scope and ownership

The user assigned G04/G05 and deferred P2 items. This record owns NAT-01..04 only, not
the broader full-suite/reset/deployment acceptance in G07. Base revision:
`2938733394a72ddf0fcfda7632a7a93bdd47a41f`, plus preserved G02/G03 work, G04 tests,
the G05 files below and documentation changes. No runtime code, dependency pins, existing
Compose profiles, existing roles or unrelated records changed.

The selected main stacks are `redmine-mcp-dev-6-0-1` and `redmine-mcp-dev-7-0-2`.
Image pins are `redmine:6.0.1@sha256:d59578dc62538c113beb983cf79eb0857715f84c5ede4e60f14ae90a0d66f05b`
and `redmine:7.0.2-bookworm@sha256:5cb12288dbfb807f136adbee02d60a96acc24edad0404cbfce214a7ced39ff6a`.
The existing guarded preparation succeeded for both; they coexist on their configured
localhost ports. Native `E2EGuard` checks running versions, synthetic markers, ownership
and project identity. Existing data was not reset. G05 creates new private projects,
ordinary users, role grants, tags, journals, activities and version containers using a
random run prefix and a private ledger. Cleanup checks project/user/role ownership before
removal and counts remaining projects, users, roles, issues, entries, versions, attachments,
journals and activities. Base fixture resources remain separate.

Final fixtures snapshot all pre-existing activity default flags and require the same values
after setup and cleanup. The caller's default activity is assigned only to the newly owned
writer role; shared enumeration flags are never used to configure the final fixture.

Both pinned targets have `redmineup_tags` **2.2.0**, `redmine_agile` **1.7.0** and
`redmine_work_time` **0.4.2**. Tests require the existing tag capability and fail setup if
missing; no plugin is installed or skipped by these cases. The plugin installer already
belongs to the selected synthetic image startup, not the fixture helper.

Main-stack settings observed: comments optional, future time allowed, cross-project issue
relations disabled. Redmine 6.0.1 has no `timelog_accept_closed_issues` setting; native time
on closed issues is accepted. Redmine 7.0.2 has that setting and initially permits it.

Alternative settings run only in randomly named `redmine-mcp-g05-policy-<version>-<run>`
stacks, with separately marked database/files volumes, private state, localhost Redmine
ports and no published PostgreSQL port. The helper refuses existing volumes and verifies
ownership labels before cleanup. A native policy script additionally requires the exact
G05 project naming pattern and dedicated environment flag before any global setting write.
Required comments and future dates are toggled on both versions; closed-issue restrictions
are toggled on 7.0.2 only. Cross-project relations are enabled there for positive cases.
The daily-hour cap is disabled only in those disposable stacks to prevent matrix entries
sharing a caller/date from interfering. The original stacks' global settings are preserved.

## Case ownership

| Owner | Cases per selected version | Plan mapping and assertions |
| --- | ---: | --- |
| `tests/e2e/test_native_variants.py` | 28 | NAT-01: two populated overlapping tags, A-only/B-only/A+B, ordinary private/restricted visibility, inherited child access, deduplication, full/one-item/empty-tail pages, counts and parent scope; native/REST/MCP parity |
| Same module: relation cases | Included above: 16 | NAT-03: four inverse types over REST/MCP, literal canonical endpoints/type/delay, same-project acceptance, native cross-project rejection under current settings, unchanged unrelated issue |
| Same module: note/watcher cases | Included above: 4 | NAT-03: own note edit, other-author denial, accepted ignored privacy field with mismatch receipt; view-only watcher denial, mutation without view, duplicate accepted no-op and unchanged control watcher set |
| Same module: attachment cases | Included above: 4 | NAT-03: issue/version update and deletion through both boundaries, native description/absence and unchanged control attachment |
| Same module: identity cases | Included above: 3 | NAT-04: ordinary locked/deleted/rotated key revocation in an established SDK session, native 401 and successful fresh rotated key |
| `tests/e2e/test_native_time_policies.py` | 12 | NAT-02: four policy/boundary matrices, each with create/update checks for comments, future dates, closed issues, explicit/default/disabled activities and minute rounding; NAT-03: eight positive cross-project inverse relation cases |
| `tests/unit/test_g05_policy.py` | 14 offline cases | Refuse either volume's foreign project/owner/version/environment labels, missing volumes, unallocated cleanup, existing-volume adoption and unsupported native scripts |

The tag reference explicitly unions independent native single-tag results, rather than
deriving expectations from the adapter. All permission-sensitive calls use newly owned
ordinary users. Administrative credentials are used only for guarded fixture setup,
native state/control inspection and cleanup. No administrator result substitutes for an
ordinary caller's authorization result.

Identity revocation may reject the SDK request at HTTP transport authentication with 401
rather than return `CallToolResult.isError`. Tests require the initial ordinary call to
succeed and the native revocation action to complete before accepting such an exception;
unrelated exceptions fail. Rotated keys regain access only through the new personal key.

## Execution

Private pytest logs/JUnit files are in `.local/testing/g05-2026-10-14/`. Native fixture,
policy, Inspector and cleanup records stay in ignored selected state directories. Logs
containing fixture keys are never copied into tracked evidence. Exact node IDs are retained
in the JUnit artifacts; the owner modules and parameterizations above identify their scope.

| Run | Result | Duration | Artifact |
| --- | --- | --- | --- |
| Offline destructive-cleanup refusals | 14 passed, no warnings | 0.17 seconds | `policy-guards.xml` |
| Final 6.0.1, both G05 modules | 40 passed; no failures/errors/skips; exit 0 | 463.34 seconds | `accepted-6.0.1.xml` |
| Final 7.0.2, both G05 modules | 40 passed; no failures/errors/skips; exit 0 | 466.59 seconds | `accepted-7.0.2.xml` |
| Inspector 2.8.0 / 6.0.1, corrected fixture | 14 calls passed; server and owned fixtures cleaned | Supplemental | `inspector-accepted-6.0.1.log` |
| Inspector 2.8.0 / 7.0.2, corrected fixture | 14 calls passed; server and owned fixtures cleaned | Supplemental | `inspector-accepted-7.0.2.log` |

Before the final fixture safety correction, both native modules passed 28 cases separately,
the corrected 6.0.1 policy matrices passed four cases, the 7.0.2 policy module passed all 12,
and both Inspector helpers passed 14 calls each. Those preliminary passes do not substitute
for the final runs above. Initial failures and targeted reruns remain in private artifacts;
they are not summed into the final accepted totals.

The source manifest is `tested-sources.sha256` in the private
artifact directory; its SHA-256 is:

```text
c1451b858fcda32ed336b6908f83ed536ad2616e37c878a77304f5b9bd1cef86
```

Inspector exercises discovery and 13 affected read/write calls through a fresh localhost
Uvicorn socket with an ordinary writer key, covering tag union, profile, note, inverse
relation creation/deletion, watcher add/remove, issue/version attachment update/deletion
and time creation/update. The separate policy matrix supplies alternate-setting evidence;
Inspector does not claim container-path, browser-download or reset acceptance.

```bash
mkdir -p .local/testing/g05-2026-10-14
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest \
  tests/e2e/test_native_variants.py --run-e2e -q
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest \
  tests/e2e/test_native_time_policies.py --run-e2e -q
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest \
  tests/e2e/test_native_variants.py --run-e2e -q
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest \
  tests/e2e/test_native_time_policies.py --run-e2e -q
uv run --frozen pytest tests/unit/test_g05_policy.py -q
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/verify-g05-inspector.py
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/verify-g05-inspector.py
```

Native runs use the same existing Pydantic deprecation warning as the offline baseline.
Scoped Ruff lint/format checks pass. The complete offline suite was not rerun for these
test-only changes; G03 remains the dated full baseline and G04 records its focused regression.

The final read-only audit verified **zero G05 policy containers, volumes or networks**,
zero remaining G05 fixture records in both main stacks, and no remaining G05 credential
configuration files. Main-stack settings still have optional comments, permitted future
dates, permitted closed-issue time where supported, disabled cross-project relations and
no shared default activity. Snapshot checks confirmed preservation of pre-existing activity
flags. Private `g05-final-audit.json` records these observations for each selected stack;
each disposable stack retains its own successful cleanup record. The tested source manifest
still matched after the final runs and documentation updates.

## Corrections and limits

Authoring exposed fixture/reference assumptions rather than runtime defects: tag plugin
callbacks require reloading an issue before setting tags; native activity names have a
30-character limit; inherited memberships must be established after parent memberships;
structured Redmine filters must include the subproject field; cross-project rejection must
respect the current setting; and session revocation can return HTTP 401. All were corrected
in the test/fixture code. The daily cap was removed only from disposable matrices, and native
time creation now supplies the same query `project_id` as the adapter so default activity
selection is compared in the same native project context.

A further review found that native `Enumeration#check_default` clears default flags across
all activities when an activity is created with `is_default=true`. Earlier fixture runs used
that callback. No pre-run flag snapshot existed; the repository's native default loader sets
no time-activity default, and the user explicitly confirmed that neither synthetic stack had
a manually configured default. No guessed default was assigned during recovery. The fixture
now creates activities with `is_default=false`, uses the owned writer role's native default,
and asserts snapshots of all pre-existing activity flags. Final acceptance requires rerunning
both versions and Inspector with this corrected fixture. Those final runs passed, including
the shared-activity preservation assertions; earlier passes remain preliminary.

This acceptance covers the named variants, not every catalog operation or workflow.
Redmine 6.0.1 cannot establish rejection under a nonexistent closed-issue setting; its
supported native behavior is checked explicitly. The broader H1..H5 criteria remain dated
except for matching scenarios above. G07's full existing live suites, explicit reset/recovery,
deployed container transport and authenticated browser byte path remain open. P2 G06/G08
are deferred by the user. No coverage percentage, threshold or testing CI claim is made.
