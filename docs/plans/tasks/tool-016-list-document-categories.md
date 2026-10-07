# tool-016-list-document-categories: List document categories

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-016-list-document-categories |
| Assigned capability | List document categories: Global enumeration lookup. |
| Type / access / destructive effects | Add reader tool / read / None |
| Status | blocked - implementation finished; testing pending |
| Dependencies | [tool-015-get-issue-write-context](tool-015-get-issue-write-context.md); prior task must have evidence and user acceptance |
| Related tasks | [Master plan](../redmine-7-0-2-capabilities.md); [dashboard](../index.md) |
| Target Redmine version | 7.0.2-bookworm pinned in synthetic Compose; exact release source reviewed, runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Read-only route, typed mapping, service/port, MCP registration, and documentation implemented. |
| Blocker / next action | Execute TOOL-016-001 through TOOL-016-005 after separate testing authorization; runtime verification remains waived. |

## 2. Discovery and evidence

The client outcome is **list document categories**. Global enumeration lookup. Do not fabricate a project-specific View documents check; return only selected public fields. No pagination contract.
Current catalog has no `list_document_categories`; it owns this public behavior exactly once.

The baseline is [tool-reference.md](../../tool-reference.md), the explicit
[MCP catalog](../../../src/redmine_mcp/mcp/catalog.py), and the router → service →
Protocol → gateway architecture. Keep unrelated working-tree edits and existing
task evidence. The existing `prep-002` offline baseline supplies future test
infrastructure. Reader access follows Redmine visibility; writers require the
separate restricted deployment and synthetic verification prerequisites.

| Source | Checked | Version claim | Relevant evidence and limitation |
|---|---|---|---|
| [Redmine reference](https://www.redmine.org/projects/redmine/wiki/Rest_Enumerations) | 2026-10-01 | General/current documentation | GET /enumerations/document_categories.json; target-build behavior must be checked in prep-005. |
| [Redmine API availability](https://www.redmine.org/projects/redmine/wiki/Rest_api) | 2026-10-01 | Enumerations API includes document categories in 7.0.2; Documents REST itself is excluded | JSON authentication, paging, upload headers, and resource availability. |
| [Repository pin](../../../deploy/compose.test.yaml) | 2026-10-02 | 7.0.2-bookworm | The pinned configuration requires runtime acceptance. |
| [Exact release archive](https://www.redmine.org/releases/redmine-7.0.2.tar.gz) | 2026-10-02 | 7.0.2 release source | `config/routes.rb` routes `enumerations/:type` to `index`; `EnumerationsController#index` accepts API authentication and returns the shared sorted subclass collection. `index.api.rsb` emits `id`, `name`, `is_default`, `active`, and visible custom values. Only the first three fields are exposed here. Runtime behavior remains unverified. |

| Decision | Resolution | Blocking? |
|---|---|---|
| Public ownership | `list_document_categories` is the sole public owner | No |
| Strict sequence | User directed continuation after tool-015 on 2026-10-02; unexecuted verification retained | No to coding |
| Testing authorization | User approves testing separately for this task | Yes to verification |
| Target version | Pinned 7.0.2 release archive inspected locally; synthetic runtime verification waived | No to coding |

## 3. Requirements

- Intended user: authenticated MCP client using the requesting Redmine identity.
- In scope: Global enumeration lookup. Do not fabricate a project-specific View documents check; return only selected public fields. No pagination contract.
- Out of scope: unrelated Redmine resources, generic forwarding, administrative
  credentials, and implicit retries. Preserve existing operation contracts.
- Permission/configuration prerequisite: Authenticated Redmine enumeration access.

| Requirement | Observable behavior |
|---|---|
| REQ-001 | List document categories produces the specified upstream mapping and typed result. |
| REQ-002 | Invalid inputs or unauthorized identity/permission do not alter protected state. |
| REQ-003 | Upstream errors, timeout, malformed results, and compatibility are handled safely. |

Illustrative synthetic input: `{}`. Illustrative selected output
fields: `{"items":[{"id":1,"name":"Uncategorized","is_default":true}],"visibility":{"scope":"requesting_redmine_user","observations":[]}}`. These examples do not assert a live result.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| MCP operation/name | list_document_categories |
| Stable operation ID | list_document_categories |
| Purpose | List document categories; Global enumeration lookup. |
| Local REST route | GET /api/v1/document-categories |
| Upstream mapping | GET /enumerations/document_categories.json |
| Authentication | Personal `X-Redmine-API-Key`; Authenticated Redmine enumeration access. |
| MCP exposure | reader; writer may reuse read route; explicit allowlist entry. |
| Annotations | readOnlyHint=true, destructiveHint=false, idempotentHint=true, openWorldHint=true. |

### Inputs and validation

| Field group | Required/default | Validation and omitted behavior | Upstream mapping |
|---|---|---|---|
| Tool arguments | No arguments | There are no path, query, or body inputs; unknown MCP arguments are rejected. | GET /enumerations/document_categories.json |
| Authentication | Required for public tools | Missing/rejected key uses existing 401 handling; no admin impersonation or key in URL. | `X-Redmine-API-Key` |

### Output and response mapping

`Collection[DocumentCategory]` with `items` holding positive `id`, nonempty `name`, and strict boolean `is_default`, plus `visibility` scoped to the requesting Redmine user. Upstream `active` and custom values are intentionally excluded. This endpoint has no pagination or count contract; an empty list is valid.
Existing REST/MCP error envelopes remain compatible. A new operation must be
registered exactly once and must not change defaults of another operation.

| Scenario | Public handling |
|---|---|
| Invalid input | Local 422 before upstream call; MCP reports tool error. |
| Missing or invalid key | Existing sanitized 401; no upstream data leaked. |
| Forbidden or absent upstream resource | Existing 403 or visibility-safe 404. |
| Redmine validation failure | Sanitized 422; no raw upstream body in logs/results. |
| Timeout, transport, oversized or malformed response | Existing 504/502-family sanitized errors; no fabricated data. |
| Other upstream status | Existing sanitized upstream error; no automatic retry. |

### Write semantics

N/A - read-only global enumeration lookup; the endpoint does not download files.

Specification exit check: the exact 7.0.2 source confirms the route, API authentication,
shared sorted enumeration, and response fields. The user directed continuation from tool-015.
No project document permission is inferred from this global lookup.

## 5. Implementation plan

| Step | Concrete change | Owner/components | Dependency and review |
|---|---|---|---|
| 1 | Confirm exact 7.0.2 endpoint, permission, response, and side effects; freeze contract. | This task document | prep-005 evidence; specification review |
| 2 | Add or extend typed models and Protocol port; preserve public defaults. | Feature models/ports | Step 1; type review |
| 3 | Map upstream request/response and sanitized errors using bounded async client. | Redmine gateway | Step 2; gateway review |
| 4 | Implement service, REST validation, and dependency wiring. | Service/router/bootstrap | Step 3; architecture review |
| 5 | Update explicit MCP catalog, application policy, and annotations if public. | MCP/auth modules | Step 4; discovery review |
| 6 | Update English tool docs and task execution record; run applicable static checks. | docs/scripts | Step 5; diff review |
| 7 | Hand off planned offline/Inspector scenarios to separately authorized testing stage. | Testing owner | User testing authorization, then user acceptance |

For a shared prerequisite, omit irrelevant public layers and record why in
the implementation review. No dependency or lockfile change is assumed;
record any newly required package and update `uv.lock` together.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Planned scenario | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | List document categories returns the expected mapped result. | TOOL-016-001 | Pending |
| AC-002 | REQ-002 | Invalid/unauthorized request is rejected without unintended mutation. | TOOL-016-002 | Pending |
| AC-003 | REQ-003 | Errors and compatibility preserve safe, truthful behavior. | TOOL-016-003/004 | Pending |
| AC-004 | REQ-001..003 | MCP discovery, invocation, and prior catalog remain correct. | TOOL-016-005 | Pending |

No criterion is accepted from a mock alone when it requires actual permission
or state verification.

## 7. Test plan and execution record

Testing is planned only. The user must authorize it separately for this task;
the repository instruction prohibits automatic unit-test verification.

| Scenario | Layer and setup | Expected result | Mode |
|---|---|---|---|
| TOOL-016-001 | Gateway/REST with exact valid payload and response; check mapped fields | Exact upstream method/path/headers, typed result, visibility or receipt | Offline; later synthetic |
| TOOL-016-002 | Missing/rejected key, wrong permission, invalid ID or body | Safe 401/403/404/422; no data leak | Offline; permission variant synthetic |
| TOOL-016-003 | Timeout, 429/5xx, malformed/oversized response | Sanitized failure and truthful outcome | Offline |
| TOOL-016-004 | Existing catalog/default/shape comparison | Prior tool behavior remains compatible | Offline MCP/REST |
| TOOL-016-005 | Startup and Inspector invocation on marked 7.0.2 fixture | MCP schema/annotations, runtime permissions | Opt-in synthetic |

| Evidence ID | Procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | Ruff lint/format, mypy, and `git diff --check` during coding | Static checks pass | Direct installed Ruff lint passed; Ruff format found 155 files formatted; mypy passed for 79 source files; `git diff --check` passed on 2026-10-02. `uv run --frozen --no-sync` could not initialize its cache under sandbox permissions. | Passed via installed executables |
| EVID-002 | `uv run --frozen pytest` after user authorizes testing | Relevant offline scenarios pass | Not run | Pending |
| EVID-003 | Inspector and marked synthetic 7.0.2 procedure after separate authorization | Required runtime cases pass | Not run | Pending |

No current 7.0.2 live or per-tool test evidence is claimed.

## 8. Implementation and review record

- Changes made: added `DocumentCategory` model, reference-data port/service/gateway method,
  REST route, explicit read-policy and MCP catalog entries, tool reference, and changelog.
- Plan deviations: reused the existing reference-data wiring; no new bootstrap dependency was needed.
- Quality: installed `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format
  --check .`, `.venv/Scripts/mypy.exe src`, and `git diff --check` passed on 2026-10-02.
  The equivalent `uv run --frozen --no-sync` commands could not initialize the external uv
  cache under sandbox permissions. Automated tests were not run.
- Startup/Inspector checks: not run.
- Documentation: this task, tool reference, changelog, and dashboard updated.
- Final code diff review: only the reference-data flow, allowlists, and related English docs
  changed. The route uses the existing `Collection` wrapper and read dependency; no prior
  operation signatures or defaults changed.
- Remaining verification: TOOL-016-001 through TOOL-016-005 remain unexecuted. Offline tests
  should check exact upstream path, selected fields, empty/malformed collections, auth and
  permission errors, timeout and oversized responses, and unchanged MCP catalog contracts.
  Startup and Inspector calls on the marked 7.0.2 fixture remain waived by the user.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass after authorization.
- [ ] Required synthetic verification and cleanup completed.
- [x] Documentation reflects implemented behavior.
- [x] Exact target version and contract reviewed from source.
- [x] Final diff reviewed and dashboard synchronized.
- [ ] User accepted this task before the next task starts.

Final status: implementation finished; testing pending. Next action: separately authorize and
execute TOOL-016-001 through TOOL-016-005; do not claim passing runtime evidence from static checks.

Target record (2026-10-02): Redmine 7.0.2 is the sole supported release. Prior runtime observations do not establish acceptance for the pinned target.

## Prep-020 evidence reconciliation, 2026-10-07

Current `list_document_categories` functional evidence is mapped in the
[32-operation ledger](../../testing/evidence/current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H2 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
