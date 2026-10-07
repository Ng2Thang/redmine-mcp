# prep-022-mcp-schema-parity: Preserve REST input contracts in MCP schemas

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-022-mcp-schema-parity |
| Assigned capability | Let an LLM invoke existing tools with every valid union and nullable input supported by REST |
| Type / access | Shared MCP prerequisite; existing read and restricted write operations |
| Destructive effects | Planning has none; subsequent authorized tool invocations retain their existing effects |
| Status | blocked |
| Dependencies | Accepted current contracts in [prep-020](prep-020-current-catalog-acceptance.md); existing prep-016/017 testing infrastructure |
| Related tasks | [Dashboard](../index.md); prep-026; tool-024/025/032/035 |
| Target Redmine version | 7.0.2; existing selected contracts accepted, new adapter behavior unverified |
| Last updated | 2026-10-07, Codex |
| Progress summary | Implementation finished; static checks passed; testing pending |
| Next action | Confirm the implementation commit, then separately authorize SCHEMA-022-001..007 verification |

## 2. Discovery and evidence

The client needs `update_issue(assigned_to_id=null)` to clear assignment, and integer or `"me"`
assignment values to reach the same REST handler. FastAPI-MCP 0.4.0 copies an OpenAPI `anyOf`
but also inserts one scalar `type`. Its type selector removes `null` and selects from a set.
SDK 1.30.0 validates both constraints before calling the REST adapter. Source inspection therefore
identifies a contract restriction; no new reproduction or test execution was performed.

| Source | Inspected | Finding / boundary |
|---|---|---|
| `mcp/registration.py`, `mcp/read_limits.py` | 2026-10-07 | Only version creation and general time-entry user IDs receive union/nullable patches before SDK caching |
| `features/issues/write_models.py`, `write_router.py` | 2026-10-07 | Clearable references accept null; assignment accepts positive integers or `me`; model validators impose additional rules |
| Installed `fastapi_mcp/openapi/convert.py:228,248`, `utils.py:4` | 2026-10-07; 0.4.0 | Generated scalar types can restrict canonical unions |
| Installed `mcp/server/lowlevel/server.py:498,536` | 2026-10-07; 1.30.0 | Input schema validation is enabled |
| [JSON Schema combinations](https://json-schema.org/understanding-json-schema/reference/combining) | 2026-10-07 | Sibling constraints also apply when `anyOf` is present; no Redmine permission claim |
| [Redmine REST API](https://www.redmine.org/projects/redmine/wiki/Rest_api), `deploy/compose.test.yaml`, [ledger](../current-catalog-acceptance.md) | 2026-10-07 | Existing native calls and pinned 7.0.2 scope remain unchanged; general API documentation is not new version-specific acceptance |

Baseline: clean working tree at `36ff5f0` when planning began. Preserve unrelated later edits.
Repository guidelines, contributor rules, the workflow and nine-section template apply.
The previous review's unknown-filter issue and the separate output-context discussion are outside
this task. Input `additionalProperties` policies and response field preservation are not changed.

| Decision | Resolution | Blocking? |
|---|---|---|
| DEC-001 | Repair from each route's canonical OpenAPI schema, never from a guessed union branch | No |
| DEC-002 | Keep SDK input validation enabled; model validators remain authoritative for cross-field/null rules not represented in OpenAPI | No |
| DEC-003 | Preserve caller inputs, route IDs, authorization, response models and existing unknown-property policies | No |

## 3. Requirements

| ID | Required observable behavior | Constraints |
|---|---|---|
| REQ-001 | Valid canonical union branches and explicit null reach REST through MCP | No adapter-invented scalar restriction |
| REQ-002 | Required fields, defaults, enum, numeric/string/array bounds and nested schemas survive conversion | No blanket removal of `type`, constraints, or validation |
| REQ-003 | SDK cache and discovery share the repaired deployment schema | Repair before cache seeding; retain caller-specific discovery isolation |
| REQ-004 | Invalid model-validator cases remain rejected without mutation | Schema repair does not promise schema-only validation of every business rule |
| REQ-005 | Existing names, permissions, output context and write receipts remain compatible | No new tool, input or upstream call |

In scope: all exposed tool input properties affected by conversion, including nested properties.
Out of scope: output passthrough/`extra_fields`, unknown-input policy changes, request body limits,
dependency upgrades, new Redmine fields and permissions.

## 4. Public contract and technical specification

| Area | Decision |
|---|---|
| Operations / REST routes | Existing 17-read/15-write catalog and registered `/api/v1/` routes; no additions or renames |
| Input defaults | Exactly those defined by each existing route/model |
| Auth / MCP exposure | Existing caller key, deployment ceiling, native permission and annotations |
| Canonical source | Route OpenAPI parameter schema and JSON request-body properties, with existing reference resolution |
| Output | Existing REST bodies and MCP text results; no output filtering or additional fields |

For every exposed operation, match its generated input properties to canonical route properties.
Restore canonical validation keywords recursively, removing an adapter-added `type` only when the
canonical node did not define it. Do not remove an authored scalar constraint merely because a
composition exists. Preserve required-property lists, defaults, aliases and schema definitions;
preserve the current tool-level unknown-property policy. Resolve references with cycle handling
compatible with existing recursive schema workarounds. Fail startup with a sanitized schema-contract
error if an exposed property cannot be matched reliably; never silently disable validation.

The existing special cases for version creation and `list_time_entries.user_id` become covered by
the shared repair. Required JSON objects and nested membership/upload/custom-field arrays keep
their native constraints. `anyOf` is not converted to `oneOf`.

Examples requiring REST/MCP parity:

```json
{"issue_id": 123, "assigned_to_id": null}
```

```json
{"issue_id": 123, "assigned_to_id": "me"}
```

Also cover numeric assignment, nullable version description/due date, and numeric/`me` general
time-entry `user_id`. Inputs forbidden by existing model validators, such as a supplied null
subject, still fail at REST even if the canonical schema alone cannot express that rule.

| Scenario | REST / MCP behavior |
|---|---|
| Schema-invalid input | Existing validation failure; MCP `isError=true`; no mutation |
| Business-rule-invalid input | Existing sanitized REST validation converted to a tool error |
| Authentication, visibility, transport or read-budget failure | Existing status/code and tool error behavior |
| Incompatible generated property | Sanitized startup failure; no partial tool catalog |

Write semantics remain single-attempt, with accepted/uncertain outcomes and independent read-back.
No write is authorized by planning. Later live write checks require an enabled owned synthetic
writer and task-owned issue cleanup. Pagination, expansion defaults and native queries are unchanged.
Specification exit: canonical schema repair and boundaries are fixed; no new native endpoint fact
is required to implement this correction.

## 5. Implementation plan

| Step | Concrete change | Ownership / dependency |
|---|---|---|
| 1 | Add canonical-property repair with deterministic recursion and reference handling | New `mcp/schema.py`; existing routing contracts/OpenAPI |
| 2 | Repair every selected tool before discovery and cache installation | `mcp/registration.py`; replace redundant per-tool union patches |
| 3 | Preserve immutable repaired schemas throughout discovery/cache use | `mcp/discovery.py`, `mcp/read_limits.py` only as necessary |
| 4 | Document restored valid inputs and remaining model-validator rules | `docs/tool-reference.md`, `CHANGELOG.md`, task/dashboard |
| 5 | Hand off scenario fixtures and test implementation separately | Existing unit/integration infrastructure; Section 7 |

Services/ports/gateways are unchanged. No dependency, lockfile, configuration or native API change
is planned. Do not edit installed packages. prep-026 later owns consolidation of private SDK access.

## 6. Acceptance criteria and traceability

| Criterion | Given / when | Then |
|---|---|---|
| AC-001 | A valid null, integer or string union branch is submitted | MCP reaches the same REST handler and returns equivalent behavior |
| AC-002 | Canonical constraints and nested objects are compared | Required/default/enum/bounds remain; unrelated schemas are unchanged |
| AC-003 | Different callers discover and invoke tools | Repaired schema survives caching without cross-caller mutation |
| AC-004 | Input violates a schema or model rule | Error is retained; upstream mutation count is zero |
| AC-005 | Catalog and receipts are compared before/after | Names, methods, gates, outputs and uncertainty semantics are preserved |

| Requirement | Criterion | Scenario | Evidence / result |
|---|---|---|---|
| REQ-001 | AC-001 | SCHEMA-022-001/002 | Pending; not run |
| REQ-002 | AC-002 | SCHEMA-022-003 | Pending; not run |
| REQ-003 | AC-003 | SCHEMA-022-004 | Pending; not run |
| REQ-004 | AC-004 | SCHEMA-022-005 | Pending; not run |
| REQ-005 | AC-005 | SCHEMA-022-006/007 | Pending; not run |

## 7. Test plan and execution record

Testing requires a separate explicit assignment. This document authorizes no test writing,
execution, application startup, Inspector or live mutations.

| Scenario | Layer / setup | Observable assertion |
|---|---|---|
| SCHEMA-022-001 | Offline ASGI and SDK; mocked issue update | Null clearing and integer/`me` assignment pass schema validation and dispatch once |
| SCHEMA-022-002 | Offline version/time-entry SDK calls | Nullable optional version fields and both user-ID branches reach REST |
| SCHEMA-022-003 | Unit/canonical schema fixtures | Nested constraints and intentionally authored `type` survive; reference cycles do not expand indefinitely |
| SCHEMA-022-004 | Offline two-caller discovery/session fixtures | Deployment cache remains immutable and repaired |
| SCHEMA-022-005 | Offline invalid subject/null, bad ID, enum and oversized array | Existing rejection; no mutation |
| SCHEMA-022-006 | Offline catalog, receipt and auth regression | Reader/writer gates, output shapes and uncertain receipts are unchanged |
| SCHEMA-022-007 | Authorized owned 7.0.2 and Inspector | Caller-owned assignment/null-clear behavior and updated discovery schema agree; restore task-owned state |

Future authorized Git Bash procedures: `bash scripts/check.sh`, targeted assigned unit/integration
tests, then SDK/Inspector scenarios against the owned environment. Run the broader offline suite
only within that verification assignment. No build is required unless packaging changes.

| Evidence | Procedure | Actual result | Status |
|---|---|---|---|
| EVID-022-001 | Read-only source/dependency inspection on 2026-10-07 | Contract restriction identified; no runtime reproduction | Planning evidence only |
| EVID-022-002 | Static checks, automated scenarios and owned live verification | Not run; authorization and implementation required | Pending |

Existing PREP-020 results are baseline evidence, not acceptance of this change.

## 8. Implementation and review record

Coding completed on 2026-10-07 against HEAD `36ff5f0`. The starting worktree contained
the staged five-task roadmap and dashboard; those planning changes were preserved.

- Added `mcp/schema.py` to match every generated property against canonical route parameters
  and JSON body properties. Canonical validation replaces adapter restrictions, while
  display titles and the current root unknown-property policy remain intact.
- Local references become tool-owned `$defs`. Reserving definitions before traversal
  terminates reference cycles without losing sibling constraints. Existing vendor-compatible
  recursive model workarounds remain necessary during initial FastAPI-MCP conversion.
- Repaired schemas are published only after the complete selected catalog matches, before
  caller discovery and SDK cache seeding. Removed the two redundant per-tool union patches.
- Updated the tool reference and changelog. No dependencies, configuration, public operation
  names, services, gateways, output models or tests changed.
- `bash scripts/doctor.sh`: required prerequisites ready.
- `uv run --frozen --no-sync ruff check .`: passed.
- `uv run --frozen --no-sync ruff format --check .`: 261 files already formatted.
- `uv run --frozen --no-sync mypy src`: passed, 121 source files.
- Final diff inspection preserves authorization, annotations, discovery ordering and existing
  membership root policy. Runtime acceptance is not established by these static results.
- `git diff --check` and `git diff --cached --check`: passed.

Testing handoff: implement and execute SCHEMA-022-001..006 with the existing offline
unit/integration infrastructure, including authored sibling constraints, cyclic local
references, immutable two-caller discovery and zero-mutation invalid inputs. SCHEMA-022-007
requires the owned pinned Redmine 7.0.2 writer and Inspector; verify resulting issue state
and restore only task-owned assignment changes. Startup, SDK calls and live checks were
not run. EVID-022-002 remains pending. No plan deviation changes the public contract.

## 9. Completion and handoff

- [x] Shared repair implemented and redundant special cases reconciled.
- [ ] Every requirement has passing named acceptance evidence.
- [ ] Assigned static, offline and owned live/Inspector checks completed.
- [x] Documentation and dashboard reflect implemented behavior.
- [x] Final diff and compatibility boundaries reviewed.

Final status: blocked for acceptance. **Implementation finished; testing pending.**
Next action: confirm the requested implementation commit and separately authorize the
SCHEMA-022-001..007 verification stage. Passing static checks do not replace that evidence.
