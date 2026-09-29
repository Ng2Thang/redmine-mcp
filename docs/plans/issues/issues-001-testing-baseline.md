# issues-001-testing-baseline: Establish mandatory offline issue-tool testing foundation

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | issues-001-testing-baseline |
| Assigned capability | Establish the mandatory baseline before dependent issue feature coding. |
| Type | shared testing prerequisite |
| Access | testing infrastructure |
| Destructive effects | None |
| Status | planned |
| Dependencies | [issues-000-policy](issues-000-policy.md) |
| Related tasks | [Backlog](index.md) |
| Target Redmine version | 6.0.5-bookworm, confirmed from compose.test.yaml |
| Last updated | 2026-09-29, redmine_feature_agent |
| Progress summary | Planning only; no acceptance evidence |
| Next action | Assign testing baseline separately; this entire task is excluded by coding-without-tests. |

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
| Local requirement | issues.md; SHA256 in analysis; 2026-09-29 | Workflow: Authorized scope and first implementation prerequisite, items 1-2 |
| Target | deploy/compose.test.yaml; 2026-09-29 | 6.0.5; reactions are deferred |
| Upstream | Versioned controller/model/show serializer linked in analysis; 2026-09-29 | Evidence/limitations retained; no live calls |
| Shared prerequisite | Workflow Authorized scope, items 1-3 | Testing foundation required before dependent feature tools |

### Questions and decisions

Specification decisions are stated below. Pending dependencies are not completed evidence.
The testing baseline is excluded from this coding assignment and must not be silently bypassed.

## 3. Requirements

Intended users are authenticated MCP/REST clients using the deployment's shared Redmine account.
In scope: Establish the mandatory baseline before dependent issue feature coding.
Out of scope: linked journals/custom-field/upload resource APIs, reaction support on 6.0.5,
individual user identities, CI, coverage thresholds and tests in this coding assignment.

| Requirement | Observable outcome | Source/prerequisite | Acceptance |
|---|---|---|---|
| REQ-001 | Establish the mandatory baseline before dependent issue feature coding. | Workflow: Authorized scope and first implementation prerequisite, items 1-2 | AC-001 |
| REQ-002 | Preserve established contracts and scope exclusions | Repository/workflow constraints | AC-002 |

Examples use only synthetic issue/project/user IDs 1/2/3, never seed fixture assumptions.
Old read arguments continue to use open status, id:asc, limit 25 and offset 0.
Read example: project_id=1,status_id='*'; get_issue issue_id=1.

## 4. Public contract and technical specification

No public tool/API changes. Add pytest and pytest-asyncio using uv and commit pyproject.toml/uv.lock together. Define offline fake settings that do not read .env; HTTPX MockTransport upstream boundary; ASGI lifespan-managed client; in-process MCP invocation. Default suite must require no network/Docker/credentials. N/A: upstream writes and tool errors.

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

Under a separate testing assignment add locked dev dependencies, offline fixtures and documented command uv run --frozen pytest; demonstrate no real settings/network leakage. No testing CI, thresholds, or packaging scope expansion.

Preserve router -> service -> port -> gateway. Services import neither HTTPX nor FastAPI.
Use Python 3.13, explicit types and lifespan-managed HTTP clients. Gate writes and keep explicit
allowlists; do not add generic CRUD. Update contract docs/changelog only for actual implemented
behavior. No dependency changes except the separately assigned testing baseline; never modify
lockfile by hand. After coding run non-installing static checks and inspect the final diff.

## 6. Acceptance criteria and traceability

| Criterion | Given | When | Then |
|---|---|---|---|
| AC-001 | Prerequisites and the setup in TEST-001 | TEST-001 procedure is performed | TEST-001: offline suite startup and fake-setting isolation holds |
| AC-002 | Compatibility/security setup in TEST-002 | TEST-002 and remaining scenarios are performed | Their explicit expected results in section 7 hold; existing defaults/security rules preserved |

| Requirement | Criterion | Method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001 | TEST-001, TEST-002, TEST-003 | Pending | Pending |
| REQ-002 | AC-002 | TEST-001, TEST-002, TEST-003 | Pending | Pending |

## 7. Test plan and execution record

TEST-001: offline suite startup and fake-setting isolation. TEST-002: REST/MCP auth and error envelopes using synthetic transports. TEST-003: cleanup closes HTTP/MCP lifecycles.

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
Next action: Assign testing baseline separately; this entire task is excluded by coding-without-tests.
