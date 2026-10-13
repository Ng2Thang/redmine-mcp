# Testing roadmap

### Issue time-entry deletion acceptance

The user separately assigned TOOL-043 testing on 2026-10-08. [Deletion evidence](testing/evidence/tool-043-testing.md)
records 32 unit cases in `tests/unit/test_time_entry_deletions.py`, 82 dedicated integration
cases in `tests/integration/test_time_entry_deletions.py`, four current-writer matrix additions,
and 1889 clean full offline regression passes. Tests exposed and fixed ignored undeclared
MCP arguments; deletion now explicitly rejects them. Native acceptance in
`tests/e2e/test_time_entry_delete_acceptance.py` passed 11 cases plus one added no-issue-view
permission case, including Inspector 2.8.0. Owned storage absence/control/totals, role boundaries,
duplicate/independent-call receipts, committed faults and moved-entry race have passing evidence.
Exact cleanup reports zero projects/entries/users/roles/activities and no private task ledger or
Inspector config remains. Scoped checks pass; injection/policy/plugin limits remain disclosed.
No final single 12-case native rerun is claimed. TOOL-041 creation remains a separate task.


The user assigned TOOL-042 testing on 2026-10-08.
[Time-entry update evidence](testing/evidence/tool-042-testing.md) records 61 unit/99 dedicated
integration cases, shared catalog fixture updates, 10 owned Redmine 7.0.2/Inspector cases and
verified zero-resource cleanup. Full offline regressions had 1,755 passes and one older reader
argument failure; its corrected rerun and seven later edge cases pass. The record does not
claim a clean full-suite rerun after final small additions/corrections. Tests use current native
settings without changing shared roles, global settings, plugins or the shared 6.0.5 server.
Broader policy/plugin/race variants and unrelated repository Ruff debt remain disclosed.

The user authorized testing for prep-022 through prep-026 on 2026-10-07.
[Preparation regression testing](testing/evidence/prep-022-026-testing.md) records the new tests,
runtime defects and corrections, owned live/Inspector results, cleanup and final offline evidence.

The user subsequently assigned PREP-027 testing on 2026-10-07.
[Read retry verification](testing/evidence/prep-027-testing.md) records deterministic retry,
budget/deadline, cancellation, identity, REST/MCP and writer receipt scenarios, adapted reader
error contracts, and read-only owned live/Inspector compatibility. Fault injection and mutations
are covered offline; the selected live checks perform zero mutations.

Current verification has three layers: unit tests, offline REST/MCP integration tests, and opt-in
live E2E against an isolated owned Redmine 7.0.2 environment. Testing CI and percentage coverage
thresholds remain deferred. The [coverage matrix](plans/testing-coverage.md) maps every current
operation and common runtime scenario to its task and selected evidence.

On 2026-10-07, [PREP-020](plans/tasks/prep-020-current-catalog-acceptance.md) reconciled the
32-operation functional catalog: **1,086 offline and 21 owned Redmine 7.0.2 live tests passed**.
The [PREP-020 ledger](testing/evidence/current-catalog-acceptance.md) records the source revision and exact
evidence, including versions, memberships, `allowed_all`, shared write uncertainty and Inspector
catalog/read compatibility. Broader historical variants remain in H1..H6; counts do not close
them automatically. No tests or runtime checks were rerun for the PREP-021 documentation update.
The registered catalog now contains 18 reads and 18 writes; consult the
[current roadmap summary](plans/index.md#current-status-2026-10-09) for later evidence and
the still-pending or waived acceptance stages. Test counts do not automatically close those gaps.

## Three-phase implementation

| Phase | Directory | Task | Environment |
|---|---|---|---|
| Unit | `tests/unit/` | [prep-016](plans/tasks/prep-016-unit-testing.md) | Fake ports, models and policies |
| Integration | `tests/integration/` | [prep-017](plans/tasks/prep-017-offline-integration-testing.md) | Mocked Redmine and in-process REST/MCP |
| E2E | `tests/e2e/` | [prep-018](plans/tasks/prep-018-live-e2e-testing.md) | Owned selected Redmine 6.x.x or 7.0.2 and PostgreSQL |

The user authorized implementation and execution on 2026-10-05. Future coding-only assignments
still require separate testing authorization. Run from Git Bash within an authorized assignment:

```bash
uv run --frozen pytest tests/unit
uv run --frozen pytest tests/integration
uv run --frozen pytest
bash scripts/check.sh
```

Default discovery selects only unit and integration. Explicit E2E selection without `--run-e2e`
exits with usage error before fixtures run. Offline fixtures disable dotenv loading, clear inherited
Redmine settings and reject real HTTPX network dispatch. Shared data and MCP session helpers are
in `tests/helpers.py`; collected test modules do not provide helpers to other modules.

### Versioned synthetic stacks

E2E uses the existing versioned Compose stacks. Preparation starts only their `postgres`
and `redmine` services, then creates the fixture data required by pytest. It does not create
another `redmine-mcp-e2e*` project, build the MCP application image, or require the large
demo/history datasets. Tests run the MCP application in process with personal user keys.

| Redmine | Compose project | Host Redmine | Host PostgreSQL | Optional reader / writer | Private E2E state |
|---|---|---|---|---|---|
| 6.0.1 | `redmine-mcp-dev-6-0-1` | `127.0.0.1:3001` | `127.0.0.1:5436` | 8002 / 8003 | `.local/e2e/redmine-mcp-dev-6-0-1/` |
| 7.0.2 | `redmine-mcp-dev-7-0-2` | `127.0.0.1:3002` | `127.0.0.1:5433` | 8000 / 8001 | `.local/e2e/redmine-mcp-dev-7-0-2/` |

Both Redmine containers listen internally on 3000. Use Docker Compose 2.24.4+. Run from Git Bash at the
repository root, with Docker Desktop running and `uv` available on `PATH`.

### Selecting a Redmine release

Run the two suites sequentially. Clear a previously exported port/image override before
using the built-in defaults:

```bash
unset REDMINE_E2E_PORT REDMINE_E2E_IMAGE
REDMINE_E2E_VERSION=6.0.1 uv run --frozen pytest tests/e2e --run-e2e
REDMINE_E2E_VERSION=7.0.2 uv run --frozen pytest tests/e2e --run-e2e
```

Pytest automatically runs `uv run --frozen python scripts/prepare-e2e.py` once per
session before live fixtures and tests. Preparation selects the existing Compose profile,
validates its image pin, synthetic markers and volumes, applies its current mounts, waits
for healthy services, and seeds six named E2E users plus role/project/issue/reporting data.
Repeated preparation verifies and reuses owned fixtures. The user-role differences needed
by permission tests remain in place. A failure aborts the session before test execution.

Offline runs, `--collect-only`, and runs with no selected E2E tests do not prepare Docker.
Selecting E2E without `--run-e2e` still fails before setup. The preparation command can
also be run separately before supplemental checks:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/prepare-e2e.py
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/verify-e2e-supplement.py
```

Set the same version/profile for preparation, pytest, and supplemental scripts. Docker
stacks may coexist, but run suites sequentially because supplemental application listeners
still use shared temporary ports. Default selection is 7.0.2. Configuration accepts exact
stable 6.x.x releases and 7.0.2; other 7.x, floating tags, prereleases and older majors fail.
Only 6.0.1 and 7.0.2 have built-in profiles. Other 6.x releases require all four settings:

| Setting | Required custom-profile value |
|---|---|
| `REDMINE_E2E_COMPOSE_FILE` | Existing repository-local override combined with `deploy/compose.yaml` |
| `REDMINE_E2E_COMPOSE_PROJECT` | Explicit Compose project name |
| `REDMINE_E2E_ENV_FILE` | Synthetic env file in ignored `.local/` or root `.env` |
| `REDMINE_E2E_PORT` | Host port 1024..65535, matching the profile's localhost-to-3000 binding |

A custom profile must include the E2E markers/project identity, read-only `/opt/testing`
mount, writable `/e2e-state` mount, and project-owned `redmine_db_data`/`redmine_files`
volumes labeled with the synthetic environment and exact version. Built-in profiles need
no env file. They use the standalone versioned Compose files and add `deploy/compose.e2e.yaml`
only during explicit E2E preparation to mount host evidence at `.local/e2e/<project>/`.
`dev-up.sh` uses named volumes and creates no host configuration or evidence directories.
Preparation supplies `REDMINE_E2E_STATE` internally; users do not set it for built-in profiles.
The official image must be `redmine:<version>[-variant]@sha256:<64-hex-digest>`.
An optional `REDMINE_E2E_IMAGE` must match that configured pin; it does not replace the image.
There is no fallback to a different release or generated standalone stack.

### Reset and migration

Normal pytest preparation does not reset the database. For a deliberate fresh start on a
selected disposable synthetic stack, use the standalone reset flag:

```bash
REDMINE_E2E_VERSION=6.0.1 uv run --frozen python scripts/prepare-e2e.py --reset
REDMINE_E2E_VERSION=7.0.2 uv run --frozen python scripts/prepare-e2e.py --reset
```

Each command stops/removes the selected project's containers, removes only its inspected
marked database/files volumes, clears that version's E2E state, and prepares new fixtures.
Other projects, env credentials, and the other version's state are retained. Preparation
restarts only PostgreSQL/Redmine; optional Docker MCP services can be started separately.
Reset refuses foreign/unmarked resources and volumes consumed by another project.

Legacy `redmine-mcp-test*` projects and volumes are left untouched. New built-in projects use
independent volumes and fixed local credentials. Stop old containers if they occupy a required
port. Demo/history manifests remain separate
and become stale after database reset: use their guarded reinitialization workflow before
running those generators again. The earlier standalone E2E stacks and `.local/testing-e2e*/`
files are not migrated or deleted automatically. Their database IDs must not be copied into
the new manifests. If an old stack occupies a required port, stop that identified stack first.

Built-in E2E manifests and logs live under `.local/e2e/<project>/`, mounted at `/e2e-state`.
Custom profiles retain `.local/e2e/<version>/`. Legacy evidence remains untouched.
Development seed state keeps its `/seed-state` mount. Missing manifests with colliding
E2E names, or a remaining `setup.json` from interrupted setup, require explicit reset;
preparation never adopts records based only on a matching name.

Diagnostics are private: `pytest-prepare.log` contains preparation output, `compose-up.log`
contains service startup output, and `seed.log` contains native fixture output.
TOOL-042/043 fixture commands also write `tool042-<action>.log` and
`tool043-<action>.log` in the selected private state directory, including failed setup
diagnostics. These logs can contain personal keys. Never paste
credentials or unredacted logs into shared evidence. Preflight checks the selected running
service/image/ports/mounts, native Redmine version, volume labels, and manifest/resource
ownership before test mutation. The MCP application still has no direct database access.

Preparation repairs category grants and expected active/closed/archived states only for
the manifest-owned baseline fixtures. Project tree positions are reloaded before state
changes, and outstanding permission reconciliation or unexpected descendants aborts setup.
Redmine 6.0.1 project responses that ignore pagination are sliced locally only when they
contain the complete counted collection with valid distinct IDs and matching pagination
echoes. Other response shapes still require strict page validation. Time-entry fixture
policies use the installed settings; an absent closed-issue time-log setting represents
the native unrestricted behavior on 6.0.1.

The adapter converts native rational hour strings such as `"5/4"` from Redmine 6.0.1
into numeric hours. Public write inputs still require JSON numbers. Receipt verification
accounts for the native whole-minute getter and the two-decimal representation used by
newer releases. Preparation also supplies the `notification` tag on the owned baseline
issue, allowing the read-only positive and negative tag controls to run against the
already-installed tag plugin instead of skipping for missing positive data.

The Compose stacks retain their declared plugins. Tag scenarios require working native
tag filtering and existing positive tag fixtures; missing prerequisites are explicitly
skipped. A skip is not compatibility acceptance. PREP-029 implementation has not been
executed against Docker or pytest; version-specific permission, state and cleanup evidence
remains pending in [the task](plans/tasks/prep-029-reuse-versioned-compose-e2e.md).

Assertions distinguish write acceptance from matched state, including accepted but ignored fields
under author/tracker restrictions. Uncertain outcomes require reconciliation before a retry.
Cleanup affects only created resources; restored fixture subjects or role grants can leave owned
journal history. Baseline fixtures and containers remain available for reruns; no reset is automatic.

The supplemental script starts a temporary localhost application on port 18081, runs Inspector
2.8.0 discovery and a read call, then uses installed Edge/Node to download an attachment through
its authenticated metadata link and compare content. It stops its application/browser and removes
the created attachment. JSON credential configs, browser profiles and redacted results stay ignored.
For interactive supplemental review:

```bash
uv run --frozen uvicorn tests.e2e.server:create_app --factory --host 127.0.0.1 --port 18081
npx @modelcontextprotocol/inspector@2.8.0
```

Connect privately to `http://127.0.0.1:18081/mcp` with an owned ordinary user's key.
Use the selected profile's Redmine URL (3001 for 6.0.1, 3002 for 7.0.2); never put keys into URLs or screenshots.

## Baseline history and further work

The [tool workflow](workflows/redmine-tools.md) requires an offline automated
baseline before dependent reader-tool implementation. The baseline uses locked pytest and
pytest-asyncio dependencies, fake settings without `.env`, HTTPX mock/ASGI transports, and MCP SDK
session checks. Run it from Git Bash without Docker or credentials:

```bash
uv run --frozen pytest
```

The historical suite covered the then-current eleven reader tools at the REST boundary and MCP discovery,
invocation, authentication, validation, and error envelopes. Authorized prep-004 work also
covers concurrent identities, bounded upstream reads, readiness, and resource cleanup.
See [the dated acceptance evidence](testing/evidence/prep-004-verification.md) for actual results and
remaining live fixture gaps. Opt-in live synthetic checks remain separate;
coverage thresholds and testing CI remain separate decisions.

Current write verification uses a separate restricted synthetic writer, disposable task-owned
resources, resulting-state checks and isolated cleanup. Existing reader credentials must remain
read-only. See the [MCP tool dashboard](plans/index.md) for dependency and scenario records.

The earlier backlog below identifies areas for further coverage, rather than declaring every
scenario untested. Consult the current ledger and original owner tasks before assigning a gap:

- Unit: service filters/defaults/pagination with fake gateways.
- Integration: mapping, upstream errors, TLS/timeouts, personal-key authentication and forwarding.
- MCP: schemas/names, error responses, shutdown and session cleanup.
- E2E: restricted projects/private issues/private journals, filters and pagination.
- Seed: reruns, interrupted writes, expected counts and access boundaries.
- Backup/restore: fresh volumes, IDs/history/permissions, attachment checksums,
  incompatible/incomplete snapshots, failure recovery.
- Packaging: isolated wheel, non-root image, import boundaries and CI.

Successful basic calls do not establish production readiness.
Operational readiness, audit/metrics, CI/package and owned recovery acceptance remain deferred
outside the current local-development roadmap; final release review remains prep-009.

## Per-user authentication scenarios for a separately authorized test stage

For future coding-only assignments, do not create or run tests without testing authorization.
The three-phase assignment above explicitly authorizes current verification. These original
authentication handoff scenarios remain useful traceability requirements:

- Two distinct keys resolve different Redmine user IDs. Interleaved and concurrent calls forward
  each key only to its own `/users/current.json` and resource requests; `me` remains upstream.
- Missing, blank, duplicate, and rejected keys return 401 before a resource request. MCP
  connection and tool discovery reject invalid keys. No key appears in tool arguments or errors.
- A malformed current-user response, timeout, transport error, and later key revocation yield
  sanitized 502, 504, 502, and 401 responses respectively.
- Visibility scope is `requesting_redmine_user`; existing operation IDs, inputs, pagination, and
  response wrappers remain stable. The write gate remains closed on reader deployments.

