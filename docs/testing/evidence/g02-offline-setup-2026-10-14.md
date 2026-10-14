# G02: Offline E2E configuration and lifecycle coverage

Date: 2026-10-14. Status: complete within the defined offline scope.

## Assignment and source

The user assigned G02 from the [coverage plan](../../plans/testing-gap-plan-2026-10-14.md)
after G01 established the existing passing offline baseline.
The work adds tests for Python configuration, ownership guards, preparation ordering,
reset boundaries and pytest opt-in behavior. No runtime, setup, native Ruby, dependency,
lockfile or existing test implementation was changed.

Base revision: `2938733394a72ddf0fcfda7632a7a93bdd47a41f`, plus the five new test/helper files
below and documentation updates. The pre-existing README and planning/evidence edits were
preserved. Private logs, collection output and fingerprints are retained in
`.local/testing/g02-2026-10-14/`.

`tested-sources.sha256` fingerprints the five new files, the Python setup/launcher modules,
the root/E2E pytest fixtures, `pyproject.toml` and `uv.lock`. Its hash is:

```text
200803ac7bb4417ffa7a17eb7598699e98d73d2d4faeef213cddad8f143322cc
```

Final fingerprint verification matched all recorded files after tests and documentation work.

The locked environment remains Python 3.13.3, pytest 9.1.1 and pytest-asyncio 1.4.0.
`bash scripts/doctor.sh` passed. Its optional checks read Docker Compose/Node/npm versions;
they did not start or inspect a stack. Git Bash required an outside-sandbox launch because
Windows denies its shared-memory initialization inside the sandbox.

## Cases and traceability

The final collection and execution contain **171 new cases: 142 unit and 29 integration**.
`tests/e2e_setup_helpers.py` supplies temporary repositories and fail-closed process/deletion
boundaries; it is not a collected test module.

| Owner | Cases | Plan / PREP-029 traceability | Behavior |
| --- | ---: | --- | --- |
| `tests/unit/test_e2e_config.py` | 48 | SET-01/02; TEST-005/007 | Built-in/default/custom selection, exact paths/commands/ports, mandatory custom fields, invalid versions, repository containment, immutable image pins and script-name injection refusal |
| `tests/unit/test_e2e_environment.py` | 81 | SET-03/05; TEST-005/006 | Compose/service/mount/volume/manifest ownership, old-version reset opt-in, missing credentials, native guard failures, reset resource selection and refusal/failure cutoffs, sanitized diagnostics and process environment |
| `tests/unit/test_local_env.py` | 13 | SET-01/03; TEST-005/007 | Shared built-in command routing, ignored terminal Compose overrides, volume ownership and owned/foreign/host port occupancy |
| `tests/integration/test_e2e_preparation.py` | 29 | SET-04/06; TEST-003/005/008 | CLI ordering/cutoffs, fresh/reused/reset orchestration, composed Python preflight with fake Docker/native output, and real child-pytest collection/session fixture behavior |

The eight child-pytest cases exercise default offline selection, unflagged E2E refusal,
collection with/without opt-in, deselected E2E, two selected cases sharing one preparation,
preparation exit failure and missing `uv`. They use copies of the repository's actual root
and E2E hooks, replacing only external preparation/native boundaries. Refusal assertions
require the opt-in usage message, so an unrelated import error cannot satisfy the test.

Four preflight integration cases execute the real Python configuration/running-volume/
container/manifest/native-inspection checks together, using only mocked Docker/native output.
They distinguish valid owned state, rejected native version/ownership, a foreign manifest
owner and malformed inspection output. No seed or mutation dispatch is permitted.

Reset cases record exact selected container IDs and database/files volume names; foreign
consumers, escaping/wrong state paths and symlink/junction flags must fail before any stop,
remove or recursive deletion. Removal failures stop later actions. The positive case records
the recursive-deletion target and preserves other-version state, backups and dotenv controls.
Symlink/junction flags are simulated; no privileged Windows link creation is required.

## Execution and corrections

| Stage | Result | Duration | Local log |
| --- | --- | --- | --- |
| First focused run | 142 passed, 10 failed | 16.23 seconds | `focused-first.log` |
| Preparation harness rerun | 25 passed | 15.66 seconds | `preparation-rerun.log` |
| Complete unit + selected related integration regression | 1,095 passed | 44.95 seconds | `regression.log` |
| Final complete G02 focused run | 171 passed | 17.08 seconds | `focused-final.log` |
| Final G02 collection | 171 collected | 0.05 seconds | `collection.log` |

The first-run failures were in the new harness: a missing `Path` import in the child shim,
a successful reset incorrectly treated as injected failure, and an overly broad sensitive
sentinel assertion matching the legitimate word `private` in a log-location message.
The harness was corrected; expected opt-in error assertions were strengthened. No setup
implementation failure was identified, and no production assertion was relaxed.

The broader passing run included all **997 current unit cases**, the then-current 25
preparation cases, and 73 existing runtime-foundation/offline-baseline integration cases.
Four composed preflight cases were added afterward and passed in the final focused run.
This is not a claim of a final 1,099-case single invocation or a complete integration rerun.

Each execution reported the existing `PydanticDeprecatedSince211` warning. Final successful
commands returned exit 0. Scoped Ruff lint and formatting checks passed for the five new
files. No mypy, architecture, coverage percentage or full business-integration pass is claimed
for this assignment; G01 remains the dated full baseline.

Run the final focused suite from Git Bash:

```bash
uv run --frozen pytest tests/unit/test_e2e_config.py \
  tests/unit/test_e2e_environment.py tests/unit/test_local_env.py \
  tests/integration/test_e2e_preparation.py -q
```

The related regression command was:

```bash
uv run --frozen pytest tests/unit tests/integration/test_e2e_preparation.py \
  tests/integration/test_runtime_foundation.py tests/integration/test_offline_baseline.py -q
```

## Completion and remaining native scope

G02 closes the missing dedicated offline Python setup/lifecycle regression coverage in F02.
PREP-029 TEST-007/008 and the Python portions of TEST-003/005/006 now have passing evidence.
PREP-029 remains in progress because its live criteria are separate.

All tested Docker/native responses and reset deletions were substituted. The only real
test subprocesses were local Python/pytest probes using temporary repositories. There was
no real stack preparation, Rails seed, Redmine request, reset, Inspector/browser call,
plugin installation or global-setting change.

Native seed idempotence, interrupted-ledger/collision handling and actual resource identities
remain PREP-029 TEST-004/G07 work. Here, incomplete seed/collision scenarios simulate a
nonzero seed result to verify the Python abort/diagnostic contract; they do not validate
the Ruby seed implementation. Native version failures likewise use a simulated guard exit.
Current two-stack coexistence, real selected reset, mount/image behavior, extra custom 6.x
deployments, native permissions and cleanup still need owned live acceptance. G03..G08 remain
separate assignments.
