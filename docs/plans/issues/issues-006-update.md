# issues-006-update: Update issue attributes and journal notes

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | issues-006-update |
| Assigned capability | Update explicitly supported issue attributes/notes without promising an atomic read-back. |
| Type | add tool |
| Access | write |
| Destructive effects | Changes issue data; journals/notifications may result |
| Status | blocked |
| Dependencies | [issues-001-testing-baseline](issues-001-testing-baseline.md), [issues-002-write-access](issues-002-write-access.md), [issues-005-create](issues-005-create.md) |
| Related tasks | [Backlog](index.md) |
| Target Redmine version | 6.0.5-bookworm, confirmed from compose.test.yaml |
| Last updated | 2026-09-29, redmine_feature_agent |
| Progress summary | Planning only; no acceptance evidence |
| Next action | Resolve field clearing, target API success and private-note permission evidence; prerequisite completion, then implement. |

## 2. Discovery and evidence

Current runtime has list_issues/get_issue, GET-only RedmineClient, one shared key/token and no
automated baseline. Relevant files: features/issues/{models,router,service,ports}.py,
integrations/redmine/{issues,client,mapping}.py, config.py, api/security.py, bootstrap.py,
mcp/registration.py and app.py. Applicable repository/contributor rules and the workflow/template
were read. Initial unrelated agent configuration/workflow changes are preserved.
See [analysis](analysis.md) for source SHA256, baseline HEAD, coverage and actual versioned URLs.
Synthetic reader has only view_issues; no writer credentials or fixtures were inspected/exposed.
The scope owner selected a separate opt-in restricted writer deployment on 2026-09-29.

| Evidence | Source/date | Finding |
|---|---|---|
| Local requirement | issues.md; SHA256 in analysis; 2026-09-29 | SRC-ISSUES-015; SRC-ISSUES-016; SRC-ISSUES-014 attachment boundary |
| Target | deploy/compose.test.yaml; 2026-09-29 | 6.0.5; reactions are deferred |
| Upstream | Versioned controller/model/show serializer linked in analysis; 2026-09-29 | Evidence/limitations retained; no live calls |
| Shared prerequisite | Workflow Authorized scope, items 1-3 | Testing foundation required before dependent feature tools |

### Questions and decisions

Contract is blocked: Resolve field clearing, target API success and private-note permission evidence; prerequisite completion, then implement.
The testing baseline is excluded from this coding assignment and must not be silently bypassed.

## 3. Requirements

Intended users are authenticated MCP/REST clients using the deployment's shared Redmine account.
In scope: Update explicitly supported issue attributes/notes without promising an atomic read-back.
Out of scope: linked journals/custom-field/upload resource APIs, reaction support on 6.0.5,
individual user identities, CI, coverage thresholds and tests in this coding assignment.

| Requirement | Observable outcome | Source/prerequisite | Acceptance |
|---|---|---|---|
| REQ-001 | Expose documented mutation | SRC-ISSUES-015; SRC-ISSUES-016; SRC-ISSUES-014 attachment boundary | AC-001 |
| REQ-002 | Reject unauthorized/invalid writes without upstream effects | Workflow authorization prerequisite | AC-002 |
| REQ-003 | Preserve uncertain outcomes, no retries and safe diagnostics | Workflow write semantics | AC-003 |
| REQ-004 | Verify resulting state and clean only task-owned resources | Workflow acceptance prerequisite | AC-004 |

Examples use only synthetic issue/project/user IDs 1/2/3, never seed fixture assumptions.
Old read arguments continue to use open status, id:asc, limit 25 and offset 0.
Creation example: issue project_id=1, subject='Synthetic task-owned issue'. Update example: notes='Synthetic note'. Destruction targets only independently created disposable IDs.

## 4. Public contract and technical specification

Proposed update_issue PUT /api/v1/issues/{issue_id}; positive ID; bearer plus write gate; writer-only operation. Body issue with optional create fields plus notes:string, private_notes:bool, start_date/due_date ISO date strings, done_ratio integer 0-100; no arbitrary editable-fields dictionary. At least one supplied field; preserve omitted attributes using exclude_unset. Explicit-null clearing semantics blocked pending target safe-attributes evidence; no guessed policy. Return acknowledged action object {issue_id:int,operation:'updated'} on verified target no-body success, public 200; do not claim current state read-back. API success status/body, private-note least permissions and uploads still need versioned evidence.

Authentication: current REST/MCP missing/invalid bearer is 401 with Bearer challenge.
Validation: malformed public inputs return 422 before upstream access.
Existing errors stay sanitized: upstream 401 -> 502 upstream_authentication; 403 ->
403 access_denied; 404 -> 404 resource_not_found; transport -> 502 upstream_unavailable;
read timeout -> 504 upstream_timeout; invalid JSON/model -> 502 upstream_response; other
unsuccessful status -> 502 upstream_error. Do not log or forward full upstream bodies.
New read-query or write validation 422 maps to sanitized upstream_validation at public 422.
MCP uses the adapter tool-error envelope, not a promised matching outer HTTP status;
later MCP scenarios must establish the actual envelope.

### Write semantics

Least permissions follow target source: create add_issues; edit_issues/edit_own_issues or
add_issue_notes depending on action; delete delete_issues. Extra watcher/private-field
permissions must be verified, not inferred from these names. Reader remains separately deployed.
No automatic retries, deduplication, rollback, or transaction guarantee. Repeated creation/notes
can duplicate state; membership/delete duplicates follow target evidence, currently unresolved.
Timeout/transport failure after sending a write may leave outcome unknown: return sanitized
write_outcome_unknown (504 timeout, 502 transport) and instruct caller to reconcile through
visible issue reads/manual verification before retrying. Successful write with later failed
read-back must not be called failed; these proposed tools perform no implicit read-back.
Concurrent edits have no local optimistic-lock guarantee; Redmine workflow remains authoritative.
Live verification/credentials/data creation are separate testing work. Cleanup acts only on
recorded task-owned IDs; deleting an issue may remove descendants and related records.

Specification exit: Not reached; named evidence/contract blockers above remain.

## 5. Implementation plan

Resolve field/null/clear and no-body success mappings with authoritative target code; extend writer port/service/gateway and client PUT; expose validated gated route and explicit writer-only MCP registration; document concurrent changes and reconciliation.

Preserve router -> service -> port -> gateway. Services import neither HTTPX nor FastAPI.
Use Python 3.13, explicit types and lifespan-managed HTTP clients. Gate writes and keep explicit
allowlists; do not add generic CRUD. Update contract docs/changelog only for actual implemented
behavior. No dependency changes except the separately assigned testing baseline; never modify
lockfile by hand. After coding run non-installing static checks and inspect the final diff.

## 6. Acceptance criteria and traceability

| Criterion | Given | When | Then |
|---|---|---|---|
| AC-001 | Prerequisites and the setup in UPDATE-001 | UPDATE-001 procedure is performed | UPDATE-001: note-only/full/sparse update leaves omitted fields untouched; validation including empty body/null and dates holds |
| AC-002 | Compatibility/security setup in UPDATE-002 | UPDATE-002 and remaining scenarios are performed | Their explicit expected results in section 7 hold; existing defaults/security rules preserved |
| AC-003 | Upstream validation/timeout/transport/unexpected response | Mutation is invoked | Sanitized errors and uncertain-outcome policy hold without retry |
| AC-004 | Disposable resources and restricted synthetic writer | Opt-in live operation and state check run | Response and actual state match; only owned resources cleaned |

| Requirement | Criterion | Method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001 | UPDATE-001, UPDATE-002, UPDATE-003, UPDATE-004 | Pending | Pending |
| REQ-002 | AC-002 | UPDATE-001, UPDATE-002, UPDATE-003, UPDATE-004 | Pending | Pending |
| REQ-003 | AC-003 | UPDATE-002 | Pending | Pending |
| REQ-004 | AC-004 | UPDATE-004 | Pending | Pending |

## 7. Test plan and execution record

UPDATE-001: note-only/full/sparse update leaves omitted fields untouched; validation including empty body/null and dates. UPDATE-002: empty upstream success, 422, 403, timeout and malformed unexpected success. UPDATE-003: repeated note invocation may create duplicate journals; no automatic retry. UPDATE-004: synthetic post-update fields/public and private notes verified, reader excluded, cleanup only owned issue.

Offline tests: pytest/pytest-asyncio with HTTPX MockTransport; ASGI explicit lifespan and
fake settings without .env; MCP client discovery/auth/invocation/envelope checks. Test default,
invalid, empty, malformed and upstream failure cases per contract. Live checks opt in to marked
synthetic environment; startup/Inspector and actual post-write state/permissions/cleanup
remain separate. N/A for docs-only interfaces where runtime scenarios do not apply.

| Evidence ID | Command/procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | uv run --frozen --no-sync ruff check . | Lint passes | Not run for implementation | Pending |
| EVID-002 | uv run --frozen --no-sync ruff format --check . | Formatting passes | Not run for implementation | Pending |
| EVID-003 | uv run --frozen --no-sync mypy src | Types pass | Not run for implementation | Pending |
| EVID-004 | git diff --check | Clean whitespace | Not run for implementation | Pending |
| EVID-005 | uv run --frozen pytest; planned scenarios | Acceptance evidence | Excluded from coding assignment | Pending |
| EVID-006 | Startup, Inspector and relevant synthetic checks | Actual behavior verified | Excluded from coding assignment | Pending |

## 8. Implementation and review record

Planning only. Review readiness is recorded separately in [review](review.md); it does not
establish code correctness or acceptance. No code/test execution evidence exists at planning.
Preserve this plan and its scenario IDs when handing off testing. Packaging acceptance, if
dependencies change, requires a later build; do not use builds as runtime verification here.

## 9. Completion and handoff

- [ ] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed.
- [ ] Documentation reflects final implemented behavior.
- [ ] No unresolved decision changes specified behavior.
- [ ] Final diff reviewed and task record synchronized.

Final status: blocked. No implementation or testing completion claimed.
Next action: Resolve field clearing, target API success and private-note permission evidence; prerequisite completion, then implement.
