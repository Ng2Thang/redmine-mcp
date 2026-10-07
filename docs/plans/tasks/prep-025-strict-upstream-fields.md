# prep-025-strict-upstream-fields: Validate known Redmine resource fields consistently

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-025-strict-upstream-fields |
| Assigned capability | Give LLMs reliable resource identities and numeric state without silently coercing malformed upstream fields |
| Type / access | Shared response-validation prerequisite; existing reads and writer observations |
| Destructive effects | No new mutation; observation failures preserve existing write acceptance |
| Status | complete |
| Dependencies | Current [prep-020](prep-020-current-catalog-acceptance.md) resource contracts; existing prep-019 receipts and prep-016/017 infrastructure |
| Related tasks | tool-011/012/034/035 strict hours/IDs; tool-033 membership models; [dashboard](../index.md) |
| Target Redmine version | 7.0.2; tested functional scope accepted |
| Last updated | 2026-10-07, Codex |
| Progress summary | Accepted: 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed |
| Next action | None in this assignment; retain regression coverage for future changes |

## 2. Discovery and evidence

Time-entry, caller-user and membership identities are already strict positive integers. Other
response models, including `Reference`, `Project`, `Issue`, journals and attachments, still use
unconstrained/coercible integers. Issue `done_ratio` has no 0..100 bound. `mapping.item` uses
ordinary `model_validate`. Thus malformed list/nested values can be coerced or accepted even where
top-level `resource_object` identity checks are strict. This is source evidence, not a new test run.

| Source | Inspected | Evidence / limitation |
|---|---|---|
| `features/projects/models.py`, `features/issues/models.py` | 2026-10-07 | Inconsistent ID/boolean/count/progress validation |
| `features/time_entries/models.py`, `users/models.py`, `projects/membership_models.py` | 2026-10-07 | Existing strict positive-ID examples to reuse |
| `integrations/redmine/mapping.py`, `responses.py`, mutation read-back gateways | 2026-10-07 | Safe 502 conversion and independently accepted writes |
| [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) | 2026-10-07 | Per-field strictness avoids unwanted coercion; blanket strict parsing may alter date behavior |
| [Redmine REST Issues](https://www.redmine.org/projects/redmine/wiki/Rest_Issues), [ledger](../../testing/evidence/current-catalog-acceptance.md) | 2026-10-07 | Existing issue representations; no new field, permission or enum claim |
| `deploy/compose.test.yaml` | 2026-10-07 | Existing 7.0.2 pin; new checks require independent acceptance |

Baseline: clean `36ff5f0`. Preserve unrelated later edits and all historical evidence. Harden only
declared fields. The user's separate output-context request must not be implemented by making
unknown response fields forbidden or by silently dropping them in a new validator.

| Decision | Resolution | Blocking? |
|---|---|---|
| DEC-001 | Use reusable per-field aliases/constraints, not blanket strict model parsing | No |
| DEC-002 | Positive resource/reference IDs reject bool/string/float/zero/negative | No |
| DEC-003 | Preserve date/hour optionality, visibility and unknown-field policy | No |
| DEC-004 | Reject malformed observation data without turning an accepted write into rejection | No |

## 3. Requirements

| ID | Required observable behavior | Constraint |
|---|---|---|
| REQ-001 | Every declared resource/reference ID is a strict positive JSON integer | Includes nested resources, parent ID, custom-field IDs and writer observations |
| REQ-002 | Declared booleans and numeric counts/progress respect their actual domain | No guessing closed native enum sets |
| REQ-003 | Missing/null/empty and valid date/hour representations preserve current semantics | Preserve explicit native omissions and visibility observations |
| REQ-004 | Malformed upstream values yield sanitized `upstream_response` errors or unavailable observations | Never expose raw data/Pydantic input; preserve receipts |
| REQ-005 | REST/MCP and valid existing fixtures retain output shape and caller authorization | No new upstream calls, inputs or fields |

Out of scope: response `extra_fields`/passthrough, global `extra="forbid"`, schema union fixes,
new enums, timestamp normalization, permissions, API expansion, general refactoring and retries.

## 4. Public contract and technical specification

| Area | Decision |
|---|---|
| Operations / REST routes | Existing resource readers and resource observations in writer results; IDs and routes unchanged |
| Inputs / defaults | Existing query/path/body contracts; HTTP query strings retain normal route conversion |
| Auth / exposure | Existing same-key reads, native visibility, reader/writer gates and catalog |
| Outputs | Same declared fields, defaults, nullability, ordering and envelopes; narrower acceptance of malformed upstream values |
| Native mapping | Existing endpoints and selected expansions; no fetch to replace missing data |

Add reusable strict-positive-ID and strict-nonnegative-integer field types in common validation
code. Apply to declared identity fields in response resources/references across projects, issues,
attachments, reference registries, users, memberships and time entries; existing stricter fields
remain strict. Public receipt IDs use the same rule where identity is exposed. Do not treat
journal detail names or relation delay as positive IDs.

Specific rules:

- `Issue.done_ratio`: strict integer in 0..100; preserve default zero when absent.
- `filesize`, `downloads` and declared count fields: strict nonnegative integers.
- Declared flags (`is_private`, `is_public`, `is_closed`, `is_default`, `private_notes`, `multiple`,
  `inherited`): strict booleans, with existing optional/default behavior.
- `Project.status`: strict positive integer; do not invent a restricted native status enum.
- Relation `delay`: strict integer when present; preserve null and signed values.
- Existing issue/time-entry hour fields: finite nonnegative JSON numbers; retain current validators.
- Existing parent mapping: keep public dictionary shape; explicitly validate its declared `id`
  as a positive strict integer without coercion or introducing a new blanket extra-key policy.

Avoid `model_validate(..., strict=True)` as a universal fix: native JSON dates are parsed from
strings and current models contain deliberate compatibility handling. Validate raw identities
before or during feature model conversion; preserve `resource_object` consistency checks.

| Scenario | REST / MCP result |
|---|---|
| Invalid declared field on a normal upstream resource read | 502 `upstream_response` with existing safe message; MCP `isError=true` |
| Invalid preflight field before a mutation | Safe upstream error; no dispatch |
| Invalid post-write observation after accepted response | Accepted receipt retained; verification unavailable; safe error where current result supports it |
| Creation success with unusable creation identity | Existing uncertain outcome, not an invented ID or automatic retry |
| Missing optional field, explicit null or valid empty collection | Existing model/visibility behavior |
| Invalid caller input or upstream auth/visibility/timeout | Existing contract unchanged |

Output unknown-field preservation remains independent. Do not add a new response-field filter or
use unknown fields in authorization/verification. Existing attachment-origin validation and safe
current-user field selection remain effective. Writer state/retry/concurrency/cleanup semantics
are unchanged; owned live checks verify that additional observation validation changes no state.
Specification exit: declared field families and error-stage distinctions are fixed.

## 5. Implementation plan

| Step | Concrete change | Files/components |
|---|---|---|
| 1 | Add narrow reusable output field types | `common/validation.py` or new common output-type module; exports |
| 2 | Apply ID/flag/count/progress rules to declared resource models | Feature models for projects/issues/attachments/reference data; reuse existing strict user/time-entry/membership fields |
| 3 | Validate parent identity without changing its public shape | Issue model validators |
| 4 | Audit conversion and raw read-back comparisons for consistent safe errors | `integrations/redmine/mapping.py`, `responses.py`, affected observation gateways |
| 5 | Preserve original receipts when validation is post-dispatch | Writer gateways and existing result contracts, no new retry path |
| 6 | Document narrower malformed-data acceptance and hand off fixtures | Tool reference/changelog/task/dashboard; tests separately assigned |

Services continue using Protocols; no FastAPI/HTTPX imports are introduced there. No dependency,
lockfile, new operation, configuration, SDK patch or upstream permission change is planned.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | Root/nested/list identity has bool, string, float, zero or negative | Resource read fails safely; valid positive integer passes |
| AC-002 | Counts/flags/progress have wrong types or ranges | Safe rejection; valid zero counts and 0/100 progress pass |
| AC-003 | Dates/hours and omitted/null/empty values are valid | Existing serialized shape and omission evidence remain |
| AC-004 | Failure is before versus after a native mutation | Zero preflight writes versus preserved accepted/uncertain receipt |
| AC-005 | Reader/writer REST and SDK fixtures are compared | Valid data, catalog, gates and unknown-field policy remain compatible |

| Requirement | Criterion | Scenario | Evidence / result |
|---|---|---|---|
| REQ-001 | AC-001 | FIELD-025-001 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |
| REQ-002 | AC-002 | FIELD-025-002 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |
| REQ-003 | AC-003 | FIELD-025-003 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |
| REQ-004 | AC-004 | FIELD-025-004 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |
| REQ-005 | AC-005 | FIELD-025-005/006 | Passed; see [verification record](../../testing/evidence/prep-022-026-testing.md) |

## 7. Test plan and execution record

The user explicitly authorized testing for prep-022 through prep-026 on 2026-10-07.
See [the verification record](../../testing/evidence/prep-022-026-testing.md) for executable coverage, corrections
and current results. Earlier coding-only prohibitions apply to that historical assignment.

| Scenario | Layer / setup | Observable assertion |
|---|---|---|
| FIELD-025-001 | Unit and MockTransport through ASGI/SDK | Parameterized root/nested/list/parent/reference/custom-field identity mutations reject without coercion |
| FIELD-025-002 | Offline wrong flags/counts/progress/status/delay | Boundaries and signed delays; no native enum invented |
| FIELD-025-003 | Offline native-style date/hour/null/missing/empty fixture | Valid parsing and exact old visibility/default/shape compatibility |
| FIELD-025-004 | Offline malformed preflight and malformed accepted read-back | Zero versus one mutation; original accepted/uncertain receipt preserved |
| FIELD-025-005 | Offline current catalog and unknown business-field fixtures | REST/MCP parity; existing extra-field policy unchanged; no auth/cache regressions |
| FIELD-025-006 | Authorized owned 7.0.2 and Inspector | Selected resource/native parity and ordinary writer read-back; clean task-owned state |

Future Git Bash procedures: `bash scripts/check.sh`, assigned output-model/reader/writer offline
cases, then authorized owned Inspector/native scenarios. Use native-shaped fixtures rather than
tests that only assert type aliases. Broader offline regressions belong to the testing assignment.

| Evidence | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-025-001 | Source inspection on 2026-10-07 | Inconsistent declared-field validation identified; no test run | Planning only |
| EVID-025-002 | Authorized offline, static and owned live/Inspector verification | 1395 offline tests and 23 owned Redmine 7.0.2 live tests including Inspector passed; static/architecture checks passed; [record](../../testing/evidence/prep-022-026-testing.md) | Passed |
| EVID-025-003 | `bash scripts/doctor.sh` in Git Bash, 2026-10-07 | Required prerequisites ready; Python 3.13.3, uv 0.12.21; no installation | Passed |
| EVID-025-004 | `uv run --frozen --no-sync ruff check .` | All checks passed | Passed |
| EVID-025-005 | `uv run --frozen --no-sync ruff format --check .` | 262 files already formatted | Passed |
| EVID-025-006 | `uv run --frozen --no-sync mypy src` | Success: no issues found in 122 source files | Passed |
| EVID-025-007 | `git diff --check` and final source/diff inspection | No whitespace errors; expected CRLF-to-LF notices only; source findings below | Passed |

## 8. Implementation and review record

Implemented on 2026-10-07 under the explicitly assigned `redmine-implement-task` coding stage.
The working-tree baseline was clean; prior task changes and acceptance evidence are preserved.

- Added and exported per-field `PositiveID` and `NonnegativeInt` in common validation code.
  Applied them to declared projects, issues, nested references, children, journals, custom fields,
  attachments, registries, users, memberships, time entries, capability reports and public
  receipt IDs. Existing strict input aliases now reuse the same positive-ID rule without
  changing caller contracts; HTTP query conversion remains untouched.
- Applied strict booleans to resource flags and receipt observations. File sizes, downloads,
  shared pagination metadata and batch indexes use strict nonnegative integers; limits remain
  positive. Issue progress is strict 0..100 with the original omitted default. Project status
  is any positive integer; relation delay is a signed strict integer or null. No enum added.
- Kept issue dates and finite nonnegative numeric hour validators intact. Parent remains
  `dict[str, int] | None`; its raw `id` must be present and strictly positive before normal
  dictionary conversion. Other dictionary keys retain the existing policy. Journal detail
  names and unstructured changesets are not reinterpreted as IDs. The existing recursive
  child schema's ID minimum now reflects the runtime constraint.
- `mapping.item` already sanitizes field-validation failures to `502 upstream_response`, so
  no blanket strict model parsing or new mapping framework was added. `resource_object` now
  also rejects nonpositive identities before expected-ID comparisons.
- Audited raw writer comparisons. Journal inventories validate journal models before extracting
  IDs; watcher inventories validate references; issue attachment container proofs validate
  attachment models and version owner references. Upload read-back now rejects nonpositive
  observed IDs in addition to its existing strict size/type checks. Duplicate and expected-ID
  checks remain. Valid native response shapes are required where old probes used sparse rows.
- Existing post-write exception boundaries retain original receipts when model conversion fails;
  memberships retain their safe observation errors and creation identity handling is unchanged.
  Issue/custom-field/upload comparisons occur only after typed issue conversion. No new read,
  mutation, retry, cache, permission path or success field was introduced. Current-user safe
  field selection and attachment-origin handling remain intact.
- Updated tool reference, manual verification, changelog and dashboard with compatibility and
  verification limitations. Unknown-field preservation/output-context work remains separate;
  no new `extra="forbid"`, passthrough or filtering behavior was added.
- Ruff formatted only changed runtime files; lint, formatting and mypy passed without suppression
  or pre-existing failures. Final source/diff review checked field coverage, parser compatibility,
  error sanitization, receipt boundaries, architecture and absence of unrelated changes/secrets.

No dependencies, lockfile, settings, SDK hooks, Docker deployment, tests, fixtures or test
infrastructure were changed. No tests, runtime probes, builds, startup, Inspector or native calls
were executed. Contract deviations: none. Runtime acceptance remains pending.

### Review follow-up: issue preflight validation

Source review identified that update and copy preflight only checked the issue's root identity,
allowing malformed declared fields to reach native dispatch. Fixed on 2026-10-07 after explicit
user authorization: both existing preflight responses now pass through
`mapping.item(IssueDetail, ...)` after `resource_object` and before mutation. Invalid progress,
flags, nested IDs or other declared fields therefore use the existing sanitized 502 boundary.
No extra upstream request is added. Normal model parsing preserves native dates/hours and
optional/default/null behavior; the raw update object remains available for field-presence and
journal comparisons. Post-write receipt handling is unchanged. Existing sparse update/copy
fixtures must provide the issue model's required native fields in the later testing assignment.

Follow-up static checks passed: `uv run --frozen --no-sync ruff check .` (all checks passed),
`uv run --frozen --no-sync ruff format --check .` (262 files already formatted),
`uv run --frozen --no-sync mypy src` (122 source files, no issues), and `git diff --check`
(no whitespace errors). Source/diff inspection confirms both validations precede dispatch and
the raw update data and post-write receipt boundaries are preserved. FIELD-025-004 must include both
update and copy with malformed preflight progress/flags/nested IDs and assert zero mutation
calls, plus valid native-shaped responses with missing/null optional fields. No tests were run.

## 9. Coding-stage handoff (superseded by section 10)

- [x] Declared output fields consistently validated (source inspection).
- [ ] Malformed identities/counts/flags/progress have passing failure evidence.
- [ ] Date/optional/visibility/shape compatibility and receipts accepted.
- [ ] Required owned native parity/cleanup recorded after authorization.
- [x] Static checks passed; documentation/final diff/task/dashboard synchronized.

Final status: blocked - **implementation finished; testing pending**. Coding/contract blockers:
none. Outstanding acceptance prerequisite: separately authorized FIELD-025-001..006 verification.

Next action: add/update offline unit and integration fixtures for FIELD-025-001..005 through
models, gateways, REST and SDK. Cover bool/string/float/zero/negative IDs at every declared depth,
strict flags, nonnegative counts/sizes, 0/100 progress, positive project status and signed/null
delays. Retain native-shaped required journal/watcher/attachment fields in existing sparse
preflight/read-back fixtures. Confirm parent shape/extra-key compatibility, dates/hours,
defaults, visibility, optional omissions/nulls, empty collections and unknown business fields.
Verify zero preflight dispatch and original accepted/uncertain receipts after invalid read-back,
including creation identities and safe membership errors. Run the selected catalog regressions
only within that testing assignment. Then separately authorize startup/Inspector and
FIELD-025-006 native parity using the owned pinned Redmine 7.0.2 reader/restricted writer
environment; observe native state and clean up only owned resources. AC-001..005 remain pending.
No build, deployment or implementation of another task is included.


## 10. Authorized testing record (2026-10-07)

The user assigned testing for all five preparation tasks. Coverage, runtime corrections,
owned fixture cleanup and final execution results are recorded in
[Preparation regression testing](../../testing/evidence/prep-022-026-testing.md). Acceptance passed: 1395 offline tests, 23 owned live tests including Inspector,
Ruff/mypy/architecture/diff checks and owned cleanup. All mapped acceptance criteria
passed within the selected functional scope. This section
supersedes the coding-stage testing handoff without removing its historical decisions.
