# PREP-029: Run E2E against the existing versioned Compose stacks

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-029-reuse-versioned-compose-e2e |
| Assigned capability | Run the same opt-in E2E suite on the existing Redmine 6.0.1 and 7.0.2 stacks without provisioning another stack |
| Type | Shared testing prerequisite; no new MCP tool |
| Access | Administrative synthetic setup, followed by existing personal-key reader/writer tests |
| Destructive effects | Fixture creation and test mutations; an explicit reset may replace only the selected synthetic stack's database/files volumes |
| Status | in progress |
| Dependencies | Existing [PREP-018 E2E baseline](prep-018-live-e2e-testing.md) and the current version-selection/automatic-preparation implementation |
| Related tasks | [Testing coverage](../testing-coverage.md), [testing roadmap](../../testing-roadmap.md) |
| Target Redmine version | Built-in 6.0.1/7.0.2; earlier 6.0.1 E2E verified on its dated setup; current self-contained layout and additional exact 6.x.x profiles pending |
| Last updated | 2026-10-14, Codex |
| Progress summary | G02 Python profile/lifecycle/reset/gate cases pass; earlier 6.0.1 result remains historical; current native layout acceptance pending |
| Next action | Verify current 6.0.1/7.0.2 native setup, seed reuse/recovery, coexistence, selected reset and browser scenarios separately |

## 2. Discovery and evidence

### G02 offline verification follow-up (2026-10-14)

The user assigned G02 from the [coverage review plan](../testing-gap-plan-2026-10-14.md).
Its final focused run passed 171 new offline cases; a broader related regression passed
1,095 before four late preflight additions. Scoped Ruff checks passed. No setup/runtime or
native Ruby code changed. [Dated evidence](../../testing/evidence/g02-offline-setup-2026-10-14.md)
records the cases, commands, corrected harness errors and mocked boundaries.

| Original scenario | Current offline evidence | Remaining scope |
| --- | --- | --- |
| TEST-003 | Preparation order/cutoffs and exactly-once session preparation pass | Confirm actual first setup and native fixture availability |
| TEST-005 | Python profile/container/volume/manifest/native-guard refusal cases pass | Native implementation/ownership behavior is simulated, not live acceptance |
| TEST-006 | Exact reset command/target selection, foreign consumers/path refusals and failure cutoffs pass | Owned real selected reset and other-stack preservation |
| TEST-007 | Built-in/custom exact-version selection and immutable pin/refusal cases pass | Runtime compatibility of additional custom releases remains separate |
| TEST-008 | Real child-pytest selection/collection/opt-in/deselection and failure gates pass with fake preparation | No native execution needed for the gate contract |

TEST-001/002/004/009 and live portions above remain pending. Simulated incomplete/colliding
seed failures verify Python abort handling; actual Ruby seed idempotence and recovery remain
TEST-004. The task remains in progress. Current built-in 7.0.2 uses host port 8001; older
3002/profile statements below retain their original planning scope.

### Current setup contract (2026-10-13)

The later self-contained development refactor supersedes the initial env-file/project layout
in this plan. Built-ins use `redmine-mcp-dev-6-0-1` and `redmine-mcp-dev-7-0-2` with their
standalone versioned Compose files, fixed local credentials, and Docker seed-state volumes.
Root `.env` and inherited Compose switches are ignored by the launcher. E2E adds
`deploy/compose.e2e.yaml` to bind `.local/e2e/<project>/` at `/e2e-state`; development startup
uses a named E2E-state volume. Custom profiles retain their explicit env-file and
`.local/e2e/<version>/` contract. Pytest prepares once before live cases; standalone
Inspector/browser scripts need explicit preparation. See the
[current instructions](../../testing-roadmap.md#selecting-a-redmine-release).

Development reset removes database/files/seed-state/named E2E-state volumes and preserves
host evidence/backups. E2E reset removes database/files and the checked host E2E state,
retaining development seed and backup volumes. Retained manifests become stale when their
database is discarded. These paths require separate acceptance of their reset boundaries.

The dated 50-case 6.0.1 result below used `redmine-mcp-test-6-0-1` before this refactor;
it is not proof of the current layout. This documentation update used manual source and
prose review only, without executing test, static-check, Docker, seed or reset commands.

### Client outcome and repository baseline

The user has prepared two versioned Docker Compose files and wants to test Redmine 6.0.1
on host port 3001 and Redmine 7.0.2 on host port 3002. Existing data in those stacks is
disposable. The initial assignment requested planning only. The user subsequently authorized
implementation of PREP-029. This coding stage excludes test execution and live Docker changes.

The current catalog remains 18 reads and 18 writes. This task changes test infrastructure;
it does not change operation IDs, API schemas, application permissions, or MCP registration.

Current `scripts/prepare-e2e.py` generates a separate Compose project under
`.local/testing-e2e*/`, starts its PostgreSQL/Redmine services, and runs native fixture seed.
`tests/e2e/conftest.py` invokes preparation once through a session autouse fixture. Existing
port defaults overlap the user's development stacks. Preflight still expects generated
Compose configuration and dedicated E2E volume names/owner labels.

The explicit 7.0.2 Compose file currently forwards 3002 to container port 3002, while its
Rails command does not select that port. Both version files publish PostgreSQL on 5436.
`scripts/common.sh` still selects `compose.test.yaml`; `dev-up.sh` and `local_env.py`
retain different default URLs/ports. Updating only the two explicit Compose files would
leave startup, preparation, and test consumers inconsistent.

The working tree already contains staged versioned Compose/plugin changes and unstaged
E2E configuration, test, script, and documentation edits. Preserve those changes and all
historical evidence. PREP-018's completed record is historical; do not rewrite it as acceptance
of this change. Repository instructions require English Markdown, Git Bash, and no automatic
test execution for this planning assignment.

### Upstream and repository evidence

| Source / versioned source | Date inspected | Version | Behavior | Permission / limitation |
|---|---|---|---|---|
| `deploy/compose.test.6.0.1.yaml` | 2026-10-12 | 6.0.1, digest `d59578dc62538c113beb983cf79eb0857715f84c5ede4e60f14ae90a0d66f05b` | Existing project `redmine-mcp-test-6-0-1`; host Redmine 3001 | Synthetic stack; source inspection only |
| `deploy/compose.test.7.0.2.yaml` | 2026-10-12 | 7.0.2-bookworm, digest `5cb12288dbfb807f136adbee02d60a96acc24edad0404cbfce214a7ced39ff6a` | Existing project `redmine-mcp-test`; intended host Redmine 3002 | Port mapping and internal URLs need correction |
| `scripts/prepare-e2e.py`, `tools/testing/e2e_config.py` | 2026-10-12 | Exact 6.x.x or 7.0.2 accepted | Generates another stack and persists an image pin | Must be replaced with selected-profile lifecycle |
| `tools/testing/*.rb`, `tests/e2e/conftest.py` | 2026-10-12 | Actual native version is checked | Native setup/inspection, fixture manifests, scoped cleanup | Currently assumes dedicated E2E owner and `/seed-state` |
| `scripts/common.sh`, `dev-up.sh`, `local_env.py` | 2026-10-12 | Built-in 6.0.1/7.0.2 | Compose routing, secrets, seed state, startup | Keep these consistent with selected profiles |

No new upstream REST semantics are proposed. Existing permission/state assertions remain
authoritative test expectations until runtime evidence identifies a version difference.
Image tags and configuration acceptance are not proof of passing compatibility.

| Client outcome | Existing coverage | Read/write | Task owner | Scope |
|---|---|---|---|---|
| Test the two existing stacks without extra Redmine/PostgreSQL containers | Auto-preparation exists but selects separate projects | Synthetic setup and tests | PREP-029 | In scope |
| Preserve broader 6.x.x configuration support | Version validator exists | Configuration only | PREP-029 | Explicit additional Compose profile required |
| Change public MCP tool behavior | Existing runtime catalog | N/A | N/A | Out of scope |

### Decisions

| ID | Question | Decision | Blocking? |
|---|---|---|---|
| DEC-001 | Which stacks own the tests? | Reuse the existing Compose projects; remove the separate generated E2E stack path from normal preparation | No |
| DEC-002 | Are current datasets valuable? | User says no; permit an explicit, selected-stack reset, without making every pytest invocation destructive | No |
| DEC-003 | Where does fixture state live? | New version-specific `.local/e2e/<version>/`, mounted at `/e2e-state`; keep application seed state at `/seed-state` | No |
| DEC-004 | Should test preparation build MCP images or generate demo datasets? | No; start only selected `postgres` and `redmine` services and seed the fixtures needed by E2E | No |
| DEC-005 | What about other 6.x releases? | Retain exact-version validation; require an explicitly configured Compose profile and pin, with no fallback to another release | No |
| DEC-006 | Can both versions run concurrently? | Both Docker stacks may stay up; run pytest and supplemental suites sequentially until shared temporary listener ports are made independent | No |

## 3. Requirements

The goal is a predictable single-command E2E run per version, using the user's two disposable
synthetic stacks. General remote Redmine access, production data, public API changes, a new
plugin integration, parallel pytest workers, and a CI version matrix are outside this task.
Do not automatically remove the earlier `redmine-mcp-e2e*` stacks or their private files.

| ID | User need | Required observable behavior | Constraint |
|---|---|---|---|
| REQ-001 | Reuse the two stacks | 6.0.1 selects host 3001; 7.0.2 selects host 3002; no third Compose project is provisioned | Start missing services within the selected project only |
| REQ-002 | Reliable automatic setup | Pytest prepares once before live fixtures/tests; setup failure aborts before tests | Retain `--run-e2e`; offline/collection-only runs cause no Docker activity |
| REQ-003 | Required test data | Seed users, roles, projects, issues, journals, time entries, and task-specific fixtures | Use separate version-specific manifest state; no demo/history seed prerequisite |
| REQ-004 | Correct target and ownership | Verify pinned image, native version, project/service identity, mounts, synthetic volume labels, and fixture ownership | Reject wrong targets before seed/test mutation |
| REQ-005 | Both stacks coexist | Redmine, PostgreSQL, and optional MCP listeners do not collide | Bind all published ports to localhost |
| REQ-006 | Disposable-data recovery | Explicit reset replaces only the selected synthetic stack; ordinary preparation reuses valid data | Never delete unrelated volumes, stack data, or other-version state |
| REQ-007 | Broader configuration compatibility | Exact 6.x.x and 7.0.2 remain valid; missing custom profile fails clearly | Never silently select 6.0.1 for a different version |
| REQ-008 | Honest verification | Logs/evidence record actual target version and skipped prerequisites | No acceptance claims from planning or unrun tests |

Examples: selecting 6.0.1 must leave the running 7.0.2 stack alone. A 6.0.1 manifest
against a 7.0.2 server must fail before writes. A missing E2E manifest with existing
unclaimed `mcp-e2e-*` resources must fail with a reset instruction rather than adopt them.

## 4. Public contract and technical specification

### Interface and target profiles

No MCP/REST contract changes. The interface is the Git Bash environment, preparation CLI,
pytest opt-in, and private fixture/evidence files.

| Setting | 6.0.1 profile | 7.0.2 profile |
|---|---|---|
| Compose files | `deploy/compose.yaml` + `deploy/compose.test.6.0.1.yaml` | `deploy/compose.yaml` + `deploy/compose.test.7.0.2.yaml` |
| Compose project | `redmine-mcp-test-6-0-1` | `redmine-mcp-test` |
| Compose env file | `.local/redmine-6.0.1/.env` | `.env` |
| Redmine host / container port | `127.0.0.1:3001` / `3000` | `127.0.0.1:3002` / `3000` |
| PostgreSQL host / container port | `127.0.0.1:5436` / `5432` | `127.0.0.1:5433` / `5432` |
| Optional MCP reader / writer host ports | `8002` / `8003` | `8000` / `8001` |
| E2E private state | `.local/e2e/6.0.1/` | `.local/e2e/7.0.2/` |
| Native fixture mount | `/e2e-state` | `/e2e-state` |

Standardize both Rails listeners, healthchecks, seed-service URLs, and container-side MCP
URLs on internal port 3000. Host URLs keep the user's 3001/3002 selection. Keep the
default `compose.test.yaml` aligned with the explicit 7.0.2 variant so legacy lifecycle
helpers cannot start an inconsistent version of the same project.

| Input | Default and validation | Behavior |
|---|---|---|
| `REDMINE_E2E_VERSION` | `7.0.2`; exact stable 6.x.x or 7.0.2 | Select a built-in profile or an explicit custom profile |
| `REDMINE_E2E_COMPOSE_FILE` | Built-in version override path | Custom 6.x profiles must specify an existing repository-local override with a matching immutable official Redmine image |
| `REDMINE_E2E_COMPOSE_PROJECT` | Built-in project name | Required with a custom file; validate Compose project syntax |
| `REDMINE_E2E_ENV_FILE` | Built-in ignored env path | Required with a custom file; file must contain a valid synthetic marker; never print its contents |
| `REDMINE_E2E_PORT` | Built-in 3001/3002 | For custom profiles, required and bounded to 1024..65535; must match the effective Compose binding; never silently rewrite an existing stack's port |
| `REDMINE_E2E_IMAGE` | Profile's Compose image | If supplied, validate the pin and require an exact match to the selected Compose image; no implicit image replacement |
| `scripts/prepare-e2e.py --reset` | Off by default; standalone operation | Validate and reset only the selected synthetic stack, then prepare fixtures; pytest never adds this flag |
| `pytest ... --run-e2e` | Explicit opt-in | Prepare once per session using the selected profile, then run preflight and tests |

Use Compose service selection (`ps -q redmine`, `exec -T redmine`) to resolve the target.
Do not assume a container name suffix or introduce extra E2E-named services. Built-in
credential initialization may reuse `local_env.py`; missing custom-profile credentials
must fail with an instruction to initialize that profile. Never regenerate database
passwords while reusing a populated volume whose credentials are unavailable.

### Preparation, fixture state, and outputs

1. Resolve and validate the selected Compose profile, env file, version/image pin, host ports,
   and any existing project/volume ownership. Save no new generated Compose stack.
2. Create the version-specific E2E state directory. Reuse the stack's existing secrets;
   initialize missing built-in configuration only when compatible with volume state.
3. Run Compose `up -d --wait` for only `postgres redmine`, installing the declared read-only
   tooling mounts and E2E environment markers through the versioned Compose configuration.
4. Inspect the selected running service and mounts, confirm its digest/version and synthetic
   environment, and use a native read-only guard before seeding.
5. Seed base/reporting fixtures under their existing scoped ownership conventions. Write
   `fixtures.json` into `/e2e-state`. Track incomplete setup with a ledger; reconcile only
   ledger-owned records or require explicit reset. Do not adopt colliding records by name.
6. Verify the resulting manifest, native resource identities, and expected fixture relationships.
   Tests and supplemental scripts then use the same service target and private directory.

Update every `tools/testing/*.rb` state path from `/seed-state` to `/e2e-state`, including
catalog evidence, permission snapshots, TOOL-042/043 manifests, and cleanup records. Do not
change the demo/history generator's `/seed-state` contract. Existing `fixtures.json` files
from the earlier separate E2E databases must never be imported as IDs for the reused stacks.

Outputs: a redacted ready message identifying release/project/URL, private manifests and
logs, and version-specific evidence. Successful setup exits zero; setup errors exit nonzero.
Keep pytest preparation output in `pytest-prepare.log` and native setup output in `seed.log`.
Supplemental factories must use preflight without implicitly seeding on import.

### Errors and reset semantics

| Scenario | Required result | Recovery |
|---|---|---|
| Unsupported version or missing/mismatched profile | Fail before Docker mutation | Correct version/profile |
| Port owned by another project | Report selected port/project without stopping that project | Correct configuration or manually stop its owner |
| Native version or image pin differs | Fail before fixture mutation | Correct selected image; use explicit reset for an approved version migration |
| Missing/mismatched synthetic marker, project, mounts, or volume labels | Refuse setup/test mutation | Correct the selected synthetic configuration; never bypass guards |
| Missing manifest with colliding/unowned fixture names | Refuse adoption | Explicit selected-stack reset |
| Seed failure or incomplete ledger | Abort before tests; retain private diagnostics | Reconcile owned state or explicitly reset |
| Inconsistent credentials after state deletion | Refuse silent password regeneration | Restore credentials or explicitly reset the selected disposable stack |

For `--reset`, inspect existing containers/volumes first and require the selected Compose
project and synthetic environment labels. Reject unmarked resources. A known prior supported
version, including the legacy 6.0.5 data under `redmine-mcp-test`, may be replaced only with
this explicit flag. Never reuse an old-major database as a shortcut for a version migration.
Stop the selected project, remove only its inspected database/files volumes, clear only its
resolved `.local/e2e/<version>/` contents, and prepare fresh data. Verify absolute deletion
targets remain under that version's E2E directory. Do not remove root `.local`, env secrets,
demo seed manifests, plugins, other projects, or the earlier standalone E2E projects.
Document that demo/history seed state is stale after an explicit database reset and requires
its own guarded reinitialization before those independent generators are used again.

Tests still clean up resources they create. Administrative setup does not grant the MCP
writer an administrator key. Preserve ordinary-user role/permission differences and the
existing accepted/ignored/uncertain write assertions. General concurrent mutation of a
selected stack and parallel E2E sessions on it are unsupported in this task.

Specification exit: configuration, ownership, and reset behavior are resolved. No new
public tool behavior or upstream permission claim needs specification.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Planned verification |
|---|---|---|---|---|
| 1 | Add shared built-in/custom profile resolution and Compose service targeting; remove normal generated-project assumptions | `tools/testing/e2e_config.py`; a shared helper under `tools/testing/` if needed | Current baseline | Profile defaults, invalid/missing custom inputs, image matching |
| 2 | Fix internal listener URLs, host port conflicts, mounts, markers, and default/explicit 7.0.2 consistency | `deploy/compose.test.6.0.1.yaml`, `compose.test.7.0.2.yaml`, `compose.test.yaml` | 1 | Effective Compose configuration and two-stack coexistence |
| 3 | Align version selection, credentials, URLs, and optional MCP reader/writer ports across existing lifecycle helpers | `scripts/common.sh`, `dev-up.sh`, `local_env.py`; dependent helpers only as needed | 1-2 | Exact selected files/project/ports; no unrelated lifecycle changes |
| 4 | Replace standalone provisioning with selected-stack start, guarded setup, and explicit reset | `scripts/prepare-e2e.py` | 1-3 | Reuse, fresh setup, missing secrets, wrong target, reset isolation |
| 5 | Move E2E state to its own mount, protect partial seed/reuse, keep role and permission fixtures | `tools/testing/*.rb` | 2, 4 | First seed, second seed, owned partial state, foreign-name refusal |
| 6 | Update preflight, service invocations, factories, tests, and supplemental tools to use one profile | `tests/e2e/*`, `scripts/verify-*.py`, `audit-catalog-acceptance.py`, `browser_check.mjs` | 1, 4-5 | Actual target/version, scoped cleanup, current behavior assertions |
| 7 | Update configuration, startup, migration, and verification documentation; preserve prior evidence | `docs/development.md`, `testing-roadmap.md`, `manual-verification.md`, coverage plan, this task and dashboard | 1-6 | Commands match final behavior; planned checks remain pending |
| 8 | Perform separately authorized offline and live verification on both releases | Scenario table below; new dated evidence | 1-7 | Record actual pass/fail/skip and cleanup; do not infer cross-version acceptance |

No runtime package or dependency change is planned. Existing pytest, HTTPX, Docker Compose,
Ruby tooling, and optional Inspector/Edge dependencies remain sufficient. Change `uv.lock`
only if implementation later establishes a necessary dependency change.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | Run E2E for 6.0.1 and then 7.0.2 | Correct existing projects serve 3001/3002; no additional Redmine/PostgreSQL project is created |
| AC-002 | Selected services are absent, stopped, or already healthy | Preparation runs once, starts/reuses only those services, and fixtures are available before tests |
| AC-003 | Repeat setup with complete owned fixture state | Native identities/relationships remain valid; no duplicate fixture records are created |
| AC-004 | Supply wrong version/image/manifest/mount/volume ownership or an unclaimed fixture collision | Fail before fixture/test writes; keep private diagnostics |
| AC-005 | Keep both stacks and optional reader/writer services running | No host port conflict; every internal URL and healthcheck reaches its intended service |
| AC-006 | Explicitly reset one marked stack with disposable old data | Only that stack's selected volumes/E2E state are replaced; the other stack and unrelated resources survive |
| AC-007 | Use another exact 6.x release with/without a valid custom profile | Explicit correct profile is used, or setup fails clearly; no fallback stack is created |
| AC-008 | Run offline discovery, `--collect-only`, unflagged E2E, or a deselected E2E suite | No preparation/seed/Docker mutation occurs; unflagged E2E is rejected |
| AC-009 | Run the suite and supplemental checks on each target | Report actual version, pass/fail/skip, permission/state outcomes, and cleanup results separately |

| Requirement | Criteria | Verification | Evidence/result |
|---|---|---|---|
| REQ-001 | AC-001 | TEST-001, TEST-002 | Pending |
| REQ-002 | AC-002, AC-008 | TEST-003, TEST-008 | Pending |
| REQ-003 | AC-002, AC-003 | TEST-003, TEST-004 | Pending |
| REQ-004 | AC-004 | TEST-005 | Pending |
| REQ-005 | AC-005 | TEST-002 | Pending |
| REQ-006 | AC-006 | TEST-006 | Pending |
| REQ-007 | AC-007 | TEST-007 | Pending |
| REQ-008 | AC-009 | TEST-009 | Pending |

## 7. Test plan and execution record

### Scenario plan

| Scenario | Criteria | Method and setup | Expected result | Mode |
|---|---|---|---|---|
| TEST-001 | AC-001 | Record project/service inventory around sequential 6.0.1 and 7.0.2 E2E invocations | Only selected existing projects start/change; correct version receives requests | Live, separately authorized |
| TEST-002 | AC-001, AC-005 | Inspect effective Compose configuration and start both selected stacks; optional MCP listeners included | Correct internal 3000 mapping, unique host ports and healthy services | Live, separately authorized |
| TEST-003 | AC-002 | Mock subprocess lifecycle for missing/stopped/healthy targets and seed failure; later confirm one real first run | Setup precedes fixtures once; seed failure aborts tests | Offline and live |
| TEST-004 | AC-003 | First seed, repeat seed, and interrupted owned fixture setup | Stable IDs and relationships; no duplicate time entries/categories/versions; safe partial-state handling | Live, separately authorized |
| TEST-005 | AC-004 | Offline profile/preflight mismatches and foreign manifests; optional marked disposable native mismatch | Reject before any mutation; no secret output | Primarily offline |
| TEST-006 | AC-006 | Reset selected marked stack and attempt reset with foreign/unmarked targets | Selected data resets; other version and foreign volumes remain; invalid targets refused | Offline boundary tests and authorized live reset |
| TEST-007 | AC-007 | Resolve supported/unsupported versions, image pins, and additional 6.x custom profiles | Exact validation and deterministic missing-profile errors | Offline |
| TEST-008 | AC-008 | Collection-only, offline, no matching live items, and missing `--run-e2e`; mock preparation dispatch | Zero preparation calls where prohibited | Offline |
| TEST-009 | AC-009 | Full selected E2E suite, Inspector/browser supplement, and cleanup review per target | Separate dated evidence; honest tag prerequisites and compatibility failures | Live, separately authorized |

Existing REST/MCP schemas, writer admission, permissions, pagination, uncertain outcomes,
and resulting-state scenarios remain in the existing suites; this task does not weaken them.
No new endpoint mapping or public model tests are required unless implementation changes
those contracts, which is outside the planned scope. Add meaningful lifecycle/profile tests
without mirroring constants as assertions.

### Commands after implementation (not executed)

Normal sequential runs, each with automatic preparation:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e --run-e2e
```

Optional explicit selected-stack reset, only when intentionally discarding its data:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/prepare-e2e.py --reset
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/prepare-e2e.py --reset
```

Supplemental checks are sequential and retain their normal optional prerequisites:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/verify-e2e-supplement.py
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/verify-e2e-supplement.py
```

| Evidence | Procedure | Expected | Actual result | Status |
|---|---|---|---|---|
| EVID-001 | Profile/lifecycle offline cases and relevant existing regressions | TEST-003, TEST-005, TEST-007, TEST-008 Python scope passes | G02: 171 final focused and 1,095 earlier related passes; see dated evidence | Accepted offline, 2026-10-14 |
| EVID-002 | Selected 6.0.1 preparation, suite, and cleanup review | Version-specific acceptance or exact failures/skips | Not run | Pending |
| EVID-003 | Selected 7.0.2 preparation, suite, and cleanup review | Version-specific acceptance or exact failures/skips | Not run | Pending |
| EVID-004 | Two-stack coexistence and explicit selected reset | TEST-002, TEST-006 pass | G02 offline reset boundaries pass; no real reset/coexistence run | Native acceptance pending |
| EVID-005 | Ruff, mypy, architecture checks, and relevant repository checks after implementation | No introduced failures | Not run | Pending |

Docker/plugin compatibility and test assumptions may fail on one version. Record and resolve
those findings rather than loosening assertions globally or presenting skipped cases as passes.
No tests, static check tools, Docker calls, seeding, resets, or live verification were executed
while preparing this plan. Repository/source inspection is planning evidence only.

## 8. Implementation and review record

Implementation authorized and completed on 2026-10-12; verification remains separate.

- Shared configuration resolves the two existing projects and complete custom 6.x profiles,
  without generated standalone Compose fallback. Native consumers use Compose service selection.
- Compose variants standardize internal port 3000, Redmine host ports 3001/3002, PostgreSQL
  ports 5436/5433, and optional MCP reader/writer ports 8002/8003 and 8000/8001. The default
  Compose file matches the explicit 7.0.2 variant. The 6.0.1 MCP listener override requires
  Compose support for the `!override` YAML tag.
- Startup/shared lifecycle helpers and synthetic env URL initialization follow the selected
  profile. Pre-existing plugin sources and unrelated staged changes were preserved.
- `tools/testing/e2e_environment.py` centralizes configuration, runtime identity, pin, native
  version, mount, volume and fixture ownership checks. Config/secrets stay in memory; public
  setup errors exclude raw subprocess output. Preparation diagnostics remain private.
- Preparation starts only selected PostgreSQL/Redmine services, seeds base/reporting fixtures,
  and verifies the manifest. Explicit `--reset` validates volume consumers, removes only
  inspected selected containers/volumes, and clears only the checked E2E state path.
- State moved to `/e2e-state` and `.local/e2e/<version>/`. Base manifests and task ledgers
  identify project/version/owner. Base resources are inspected before repairs. Initial setup
  uses a transaction and incomplete-setup ledger. Failed or unclaimed fixture state requires
  explicit reset rather than name-based adoption.
- Existing E2E helpers/factories use the selected service and project identity. Task-native
  JSON parsing tolerates preceding plugin notices without printing private keys.
- Documentation updated: development, testing roadmap, manual verification, coverage matrix,
  task, and dashboard. Historical acceptance records remain unchanged.
- Source diff reviewed manually. No new lifecycle/profile unit tests were added or executed;
  TEST-003, TEST-005, TEST-007, and TEST-008 coverage is handed off to verification.
- A scoped Ruff lint command was attempted but rejected by automatic approval review before
  execution because repository instructions require authorization for verification tools.
  Ruff, mypy, format/architecture checks, and runtime checks remain unrun. The rejected
  command also included shell paths; a future authorized Ruff invocation must select only
  Python files. No alternate check route was used.
- No Docker commands, seed scripts, resets, Inspector, browser checks, or pytest were run
  during implementation. The user-observed port collision is prior evidence, not a new run.
- Plan limitation: existing volumes with a missing env file require restoring their original
  marked env file before setup/reset; replacement database passwords are never invented.
- Remaining blocker: static-check authorization and TEST-001..009 acceptance evidence.

## 9. Completion and handoff

### Initial diagnosis on 2026-10-13, before test execution authorization

- The user supplied a failing E2E summary and explicitly authorized API GET diagnostics.
  Only existing source/log inspection and API GET requests were performed; no pytest,
  lint/type checks, Rails runner, seed, reset, or container lifecycle changes were executed.
- On the installed 6.0.1 server, `projects.json?limit=1&offset=0` returned nine projects
  for the ordinary fixture user and 21 for the administrator, while echoing `limit: 1`.
  Offset 1 also returned the complete collection. Installed `ProjectQuery.results_scope`
  did not apply the supplied pagination options. Project reads now slice a response only
  when it contains the complete counted collection, matching integer pagination echoes,
  and distinct positive project IDs. Other endpoints retain strict page validation, and
  existing response-byte, request, deadline, and query-depth budgets remain enforced.
- Installed 6.0.1 settings and time-entry validation have no
  `timelog_accept_closed_issues` setting or corresponding closed-issue restriction.
  TOOL-042/043 fixtures now record the native unrestricted behavior when that getter is
  absent, and use the actual getter when available.
- Installed category routes use `manage_categories`. Owned writer fixture preparation
  now adds the available category permission names for both fresh and existing fixtures.
- API GET showed the intended closed fixture active (status 1) and fixture b closed
  (status 5). Seed project objects retained obsolete nested-set positions after creation
  and reparenting. Preparation now reloads projects before descendant operations and
  restores the owned baseline states transactionally, checking descendant ownership and
  refusing outstanding permission reconciliation. This repair has not been executed.
- TOOL-042/043 helpers now save captured stdout/stderr to private per-action log files;
  assertion messages contain only the log path. Setup exceptions no longer lose their
  diagnostics when no ledger was written or a failed setup removed its ledger.
- Full-suite failures, including the reporting and Inspector failures, remain pending
  re-execution after these changes; the supplied summary alone does not prove that every
  failure shares one of the diagnosed causes. No passing acceptance is claimed.

### Authorized execution on 2026-10-13

The user subsequently authorized running and fixing the complete 6.0.1 E2E command,
and separately authorized Ruff and mypy. The final exact command exited zero with
**50 passed, no failed or skipped cases**, and one Pydantic deprecation warning in
624.41 seconds. Both time-entry cleanup records report zero remaining resources.
Native rational-hour conversion and owned positive tag seeding resolved the remaining
failures/skips. Changed Python lint/format and runtime mypy pass; repository-wide mypy
still reports four errors in the separate documentation package. See the dated
[6.0.1 evidence](../../testing/evidence/prep-029-redmine-6.0.1.md) for commands, module
counts, fixes, private log locations, and verification limits.

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Live permission/state checks, coexistence, and selected reset verified.
- [x] Documentation reflects the implemented behavior.
- [x] Contract decisions and dependency order recorded.
- [x] Task and dashboard planning status synchronized.

Final status: in progress (6.0.1 full E2E verified; broader PREP-029 acceptance pending).

Outcome: E2E preparation targets the existing 6.0.1 and 7.0.2 stacks and private fixture
state, with an explicit guarded selected-stack reset. The complete selected 6.0.1 E2E
suite passes, including Inspector and tag controls. No 7.0.2/reset acceptance is claimed.

Next action: implement/run the remaining offline lifecycle scenarios and verify 7.0.2,
coexistence, selected reset, and browser supplements in separate assignments. The 6.0.1
portion of EVID-001 and relevant scoped static checks have passing evidence; the broader
EVID-001..005 requirements remain incomplete.
