# issues-004-detail: Expose supported issue detail expansions

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | issues-004-detail |
| Assigned capability | Allow caller-selected detail includes and retain current journals/attachments default. |
| Type | extend existing tool |
| Access | read |
| Destructive effects | None |
| Status | planned |
| Dependencies | [issues-000-policy](issues-000-policy.md), [issues-001-testing-baseline](issues-001-testing-baseline.md), [issues-003-list](issues-003-list.md) |
| Related tasks | [Backlog](index.md) |
| Target Redmine version | 6.0.5-bookworm, confirmed from compose.test.yaml |
| Last updated | 2026-09-29, redmine_feature_agent |
| Progress summary | Planning only; no acceptance evidence |
| Next action | Implement after mandatory testing foundation and shared list model task; reaction support remains deferred. |

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
| Local requirement | issues.md; SHA256 in analysis; 2026-09-29 | SRC-ISSUES-008 through SRC-ISSUES-012; SRC-ISSUES-020 |
| Target | deploy/compose.test.yaml; 2026-09-29 | 6.0.5; reactions are deferred |
| Upstream | Versioned controller/model/show serializer linked in analysis; 2026-09-29 | Evidence/limitations retained; no live calls |
| Shared prerequisite | Workflow Authorized scope, items 1-3 | Testing foundation required before dependent feature tools |

### Questions and decisions

Specification decisions are stated below. Pending dependencies are not completed evidence.
The testing baseline is excluded from this coding assignment and must not be silently bypassed.

## 3. Requirements

Intended users are authenticated MCP/REST clients using the deployment's shared Redmine account.
In scope: Allow caller-selected detail includes and retain current journals/attachments default.
Out of scope: linked journals/custom-field/upload resource APIs, reaction support on 6.0.5,
individual user identities, CI, coverage thresholds and tests in this coding assignment.

| Requirement | Observable outcome | Source/prerequisite | Acceptance |
|---|---|---|---|
| REQ-001 | Allow caller-selected detail includes and retain current journals/attachments default. | SRC-ISSUES-008 through SRC-ISSUES-012; SRC-ISSUES-020 | AC-001 |
| REQ-002 | Preserve established contracts and scope exclusions | Repository/workflow constraints | AC-002 |

Examples use only synthetic issue/project/user IDs 1/2/3, never seed fixture assumptions.
Old read arguments continue to use open status, id:asc, limit 25 and offset 0.
Read example: project_id=1,status_id='*'; get_issue issue_id=1.

## 4. Public contract and technical specification

Keep get_issue GET /api/v1/issues/{issue_id}, positive int ID, Issue result. Add optional include CSV enum children,attachments,relations,changesets,journals,watchers,allowed_statuses; omission uses journals,attachments; explicit empty string requests no expansions, duplicate allowed values deduplicate. Reject unknown/reactions 422 before upstream (6.0.5 compatibility). Upstream GET issues/{id}.json omits include for explicit empty. Add Issue children/changesets as list[dict[str,JsonValue]] with default empty arrays (preserve upstream nested detail shapes without inventing required keys); watchers list[Reference]; allowed_statuses list[IssueStatusReference] with id/name/is_closed; relations shared with list task. Pydantic typed JsonValue bounds generic response content to JSON only. No local workflow prediction, user enrichment, permission bypass, or field removal. Existing get error mappings unchanged. No write semantics.

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

N/A for this task: it does not invoke upstream mutations; configuration prerequisite merely gates future routes.

Specification exit: Decisions complete for this task; dependencies and acceptance pending.

## 5. Implementation plan

Extend shared response models only after list owner; add include argument through router/service/port/gateway; revise caller description and public docs to distinguish omitted expansions from absence of associated data; keep MCP allowlist/name.

Preserve router -> service -> port -> gateway. Services import neither HTTPX nor FastAPI.
Use Python 3.13, explicit types and lifespan-managed HTTP clients. Gate writes and keep explicit
allowlists; do not add generic CRUD. Update contract docs/changelog only for actual implemented
behavior. No dependency changes except the separately assigned testing baseline; never modify
lockfile by hand. After coding run non-installing static checks and inspect the final diff.

## 6. Acceptance criteria and traceability

| Criterion | Given | When | Then |
|---|---|---|---|
| AC-001 | Prerequisites and the setup in SHOW-001 | SHOW-001 procedure is performed | SHOW-001: omitted input retains current expansions; explicit empty omits upstream include holds |
| AC-002 | Compatibility/security setup in SHOW-002 | SHOW-002 and remaining scenarios are performed | Their explicit expected results in section 7 hold; existing defaults/security rules preserved |

| Requirement | Criterion | Method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001 | SHOW-001, SHOW-002, SHOW-003, SHOW-004 | Pending | Pending |
| REQ-002 | AC-002 | SHOW-001, SHOW-002, SHOW-003, SHOW-004 | Pending | Pending |

## 7. Test plan and execution record

SHOW-001: omitted input retains current expansions; explicit empty omits upstream include. SHOW-002: supported combinations preserve nested values; watcher omission by upstream permissions; workflow-specific allowed statuses forwarded unchanged. SHOW-003: reactions/unknown/invalid ID rejected before upstream; auth, absent resource, malformed data and MCP envelope. SHOW-004: synthetic visibility/private journal boundaries.

Offline tests: pytest/pytest-asyncio with HTTPX MockTransport; ASGI explicit lifespan and
fake settings without .env; MCP client discovery/auth/invocation/envelope checks. Test default,
invalid, empty, malformed and upstream failure cases per contract. Live checks opt in to marked
synthetic environment; startup/Inspector and read visibility/permissions
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

Final status: planned. No implementation or testing completion claimed.
Next action: Implement after mandatory testing foundation and shared list model task; reaction support remains deferred.
