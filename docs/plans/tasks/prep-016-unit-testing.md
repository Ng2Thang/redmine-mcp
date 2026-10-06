# prep-016-unit-testing: Unit testing

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-016-unit-testing |
| Capability | Unit contracts without frameworks or upstream access |
| Type | Testing implementation and explicitly authorized verification |
| Access / destructive effects | Offline only / none |
| Status | complete |
| Dependencies | prep-002 completed offline baseline |
| Related tasks | prep-014, prep-015, tool-001 through tool-031; [coverage matrix](../testing-coverage.md) |
| Target | Redmine 7.0.2 |
| Last updated | 2026-10-06 |
| Progress | Required selected scenarios pass; evidence recorded below |
| Next action | Maintain the matrix when tools or runtime contracts change |

## 2. Discovery and evidence

The user explicitly authorized implementation of all three phases and their planned execution.
The working tree was clean at assignment start. The historical prep-004 record reports 356 passing
offline tests against the then-current reader contract. Current code registers 15 reader and 11
writer operations. That historical result is preserved, not treated as current acceptance.

Source evidence: current catalog, feature models/services, Redmine gateways, existing tests,
`deploy/compose.test.yaml`, the nine-section task template and tool workflow. The target image's
embedded `lib/redmine/version.rb` declares 7.0.2; inspected on 2026-10-05. Live permission fixtures
use the same pinned image's Role model and native administrative fixture path.

The pre-existing shared synthetic environment runs 6.0.5. It remains separate from the owned
`redmine-mcp-e2e` project. All generated configuration, credentials, downloads and logs are ignored.

## 3. Requirements

| Requirement | Observable behavior |
|---|---|
| REQ-001 | Services reject invalid input or known permission denials before gateway dispatch; omission/null/empty and exact budget boundaries match the public contract. |
| REQ-002 | Every current tool and shared requirement maps to selected scenarios and evidence. |
| REQ-003 | Default discovery remains offline; live tests require explicit selection and `--run-e2e`. |
| REQ-004 | Historical tests/evidence remain traceable; known intentional compatibility changes use current expectations. |

Scope is the application and its 26 current operations. CI, percentage thresholds, production
verification, backup/restore and general seed-tool acceptance are deferred. Administrative E2E
fixture provisioning is included; it does not use the MCP application key.

## 4. Public contract and technical specification

No application API changes. Tests consume existing typed service, REST and MCP interfaces.
Shared fixture coordination stays in `tests/conftest.py`; reusable synthetic data and SDK sessions
live in `tests/helpers.py`. Tests use package-qualified imports rather than importing helpers from
test modules. The implementation directory is `tests/unit/`.

Offline tests disable dotenv loading, clear inherited REDMINE settings and reject real HTTPX
network transports. Integration clients use MockTransport or ASGITransport with explicit lifespan;
streaming mocks emulate an open upstream response for admission/cleanup assertions.

Live tests explicitly inspect the image pin, container/volume ownership labels, synthetic marker,
private manifest and project identifiers. `scripts/prepare-e2e.py` creates only the isolated E2E
project on localhost port 3001. Its native fixture scripts are guarded by owner and target version.
The MCP application accesses Redmine only through HTTP; administrative fixture inspection handles
archived/module-disabled objects that even the admin REST API cannot read.

Live writes are single attempts. Receipts and resulting state are separate assertions: an accepted
but ignored field must report mismatch; forbidden writes must leave state unchanged. Uncertain
creates require reconciliation before retry. Cleanup tracks only resources created by the test;
owned fixture journals can remain. Temporary application/browser processes are stopped after use.

## 5. Implementation plan

1. Audit the shared coverage matrix and classify existing tests by exercised boundary.
2. Preserve and migrate existing assertions; update obsolete catalog and continuation expectations.
3. Implement preserved validation/service tests; new writer, settings, budget and capability tests.
4. Keep execution gates, private fixtures and cleanup separate from application runtime changes.
5. Run the assigned suite and required static checks; record actual results and limitations.
6. Synchronize this task, testing guidance and the dashboard.

Reuse locked pytest, pytest-asyncio, HTTPX and MCP tooling; no dependency upgrade, hook installation
or CI configuration is included. Supplemental checks reuse Inspector 2.8.0 and installed Edge/Node.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Acceptance | Evidence |
|---|---|---|---|
| AC-001 | REQ-001 | Services reject invalid input or known permission denials before gateway dispatch; omission/null/empty and exact budget boundaries match the public contract. | UNIT-001; passing record in section 7 |
| AC-002 | REQ-002 | All current operations and common policies have an explicit scenario owner. | Coverage matrix |
| AC-003 | REQ-003 | Default collection excludes live tests; unflagged live selection exits with usage error before fixtures. | GATE-001 |
| AC-004 | REQ-004 | Original 356 tests remain represented; dated historical records are intact. | Migration/source audit |

## 7. Test plan and execution record

| Scenario | Method and expected result |
|---|---|
| UNIT-001 | `uv run --frozen pytest tests/unit`; selected contract assertions pass. |
| GATE-001 | Select `tests/e2e` without `--run-e2e`; exit 4 before live fixture execution. |
| STATIC-001 | `bash scripts/check.sh`; Ruff, formatting, runtime mypy and architecture checks pass. |
| TRACE-001 | Compare operation catalog against the shared coverage matrix and scenario tables. |

Detailed cases and implementation names are in the [coverage matrix](../testing-coverage.md).
Live acceptance additionally uses `uv run --frozen python scripts/verify-e2e-supplement.py` for
Inspector discovery/call and an authenticated browser attachment download with content comparison.
Its JSON config and credentials remain in ignored `.local/testing-e2e`, never CLI key arguments.

Execution evidence, 2026-10-06: 102 unit cases pass in default offline discovery.
The default `uv run --frozen pytest` run passes all 497 offline cases. Its JUnit record
is `.local/testing-e2e/offline-results.xml`; live evidence is `live-results.xml` in the same
ignored directory. Explicit unflagged E2E collection exits 4 before fixtures.
`bash scripts/check.sh` passes Ruff, formatting, runtime mypy and architecture checks.
Inspector 2.8.0 returns the exact 26-tool catalog and visible project data; installed Edge
downloads the authenticated attachment and matches its bytes. Supplemental process and
owned resource cleanup pass; redacted status is `supplement-evidence.json`.
One existing upstream Pydantic deprecation warning remains; it does not fail acceptance.

## 8. Implementation and review record

Implemented: Preserved validation/service tests; new writer, settings, budget and capability tests. Existing helper imports and pytest discovery were reorganized.
No application source or public tool contract was changed. Successful fixture calls do not imply
production readiness or exhaustive combinations of every Redmine workflow.

Observed target behavior includes archived/disabled REST denial and accepted but ignored updates
under own-only or tracker restrictions. These are asserted through resulting-state checks instead
of inventing a 403 for every rejected field. Live fixture setup persists distinct public/private
journals and repairs inherited roles after parent memberships exist; interrupted preparation
can resume owned resources.

## 9. Completion and handoff

- [x] Assigned test implementation and fixtures are present.
- [x] Current operation/scenario ownership is documented.
- [x] Required tests and static checks have final passing evidence.
- [x] Required supplemental checks pass where applicable.
- [x] Final diff, documentation and dashboard are synchronized.

Final status: complete for the named three-phase scenarios. Historical application task
matrices retain broader pending variants. CI, coverage thresholds, production, seed-tool
and backup/restore acceptance remain deferred. The lost-response live scenario injects
a transport fault after a real Redmine commit; it does not reproduce every network failure.
Owned fixture journals and the isolated environment remain for repeatable reruns.
