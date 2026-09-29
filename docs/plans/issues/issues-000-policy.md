# issues-000-policy: Reconcile current capabilities and authorized future scope

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | issues-000-policy |
| Assigned capability | Make repository policy truthful about current read-only runtime and authorized issue writes/testing, without claiming unimplemented infrastructure exists. |
| Type | shared prerequisite |
| Access | read-only documentation |
| Destructive effects | None |
| Status | blocked |
| Dependencies | None |
| Related tasks | [Backlog](index.md) |
| Target Redmine version | 6.0.5-bookworm, confirmed from compose.test.yaml |
| Last updated | 2026-09-29, redmine_feature_agent |
| Progress summary | Independent policy documentation coding finished; static environment and acceptance pending |
| Next action | Provide Python 3.13/static tools, rerun checks; separately assign testing foundation |

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
| Local requirement | issues.md; SHA256 in analysis; 2026-09-29 | Workflow: Authorized scope and first implementation prerequisite |
| Target | deploy/compose.test.yaml; 2026-09-29 | 6.0.5; reactions are deferred |
| Upstream | Versioned controller/model/show serializer linked in analysis; 2026-09-29 | Evidence/limitations retained; no live calls |
| Shared prerequisite | Workflow Authorized scope, items 1-3 | Testing foundation required before dependent feature tools |

### Questions and decisions

Specification decisions are stated below. Pending dependencies are not completed evidence.
The testing baseline is excluded from this coding assignment and must not be silently bypassed.

## 3. Requirements

Intended users are authenticated MCP/REST clients using the deployment's shared Redmine account.
In scope: Make repository policy truthful about current read-only runtime and authorized issue writes/testing, without claiming unimplemented infrastructure exists.
Out of scope: linked journals/custom-field/upload resource APIs, reaction support on 6.0.5,
individual user identities, CI, coverage thresholds and tests in this coding assignment.

| Requirement | Observable outcome | Source/prerequisite | Acceptance |
|---|---|---|---|
| REQ-001 | Make repository policy truthful about current read-only runtime and authorized issue writes/testing, without claiming unimplemented infrastructure exists. | Workflow: Authorized scope and first implementation prerequisite | AC-001 |
| REQ-002 | Preserve established contracts and scope exclusions | Repository/workflow constraints | AC-002 |

Examples use only synthetic issue/project/user IDs 1/2/3, never seed fixture assumptions.
Old read arguments continue to use open status, id:asc, limit 25 and offset 0.
Read example: project_id=1,status_id='*'; get_issue issue_id=1.

## 4. Public contract and technical specification

No tool, route, MCP operation, payload, or runtime setting changes. N/A: API input/output/error/write semantics. Preserve current read-only reader guidance. State that dedicated writer deployments and automated issue-tool acceptance testing are authorized future work; coverage and CI remain deferred. The coding-only assignment still excludes testing work.

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

Update AGENTS.md, CONTRIBUTING.md, development/testing-roadmap, SECURITY.md, architecture, and configuration guidance with current versus authorized scope. Preserve all existing security constraints and current tool catalog.

Preserve router -> service -> port -> gateway. Services import neither HTTPX nor FastAPI.
Use Python 3.13, explicit types and lifespan-managed HTTP clients. Gate writes and keep explicit
allowlists; do not add generic CRUD. Update contract docs/changelog only for actual implemented
behavior. No dependency changes except the separately assigned testing baseline; never modify
lockfile by hand. After coding run non-installing static checks and inspect the final diff.

## 6. Acceptance criteria and traceability

| Criterion | Given | When | Then |
|---|---|---|---|
| AC-001 | Prerequisites and the setup in DOC-001 | DOC-001 procedure is performed | DOC-001: inspect each policy for consistency; no claim of installed pytest or active writes holds |
| AC-002 | Compatibility/security setup in DOC-002 | DOC-002 and remaining scenarios are performed | Their explicit expected results in section 7 hold; existing defaults/security rules preserved |

| Requirement | Criterion | Method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001 | DOC-001, DOC-002 | Pending | Pending |
| REQ-002 | AC-002 | DOC-001, DOC-002 | Pending | Pending |

## 7. Test plan and execution record

Runtime/API scenarios, pytest, Inspector and live checks are N/A for policy text itself.
DOC-001/002 are document/diff inspection criteria; no executable tests are introduced.

DOC-001: inspect each policy for consistency; no claim of installed pytest or active writes. DOC-002: current reader setup, secrets, and localhost restrictions remain intact.

Offline tests: pytest/pytest-asyncio with HTTPX MockTransport; ASGI explicit lifespan and
fake settings without .env; MCP client discovery/auth/invocation/envelope checks. Test default,
invalid, empty, malformed and upstream failure cases per contract. Live checks opt in to marked
synthetic environment; startup/Inspector and read visibility/permissions
remain separate. N/A for docs-only interfaces where runtime scenarios do not apply.

| Evidence ID | Command/procedure | Expected | Actual | Status |
|---|---|---|---|---|
| EVID-001 | UV_OFFLINE=true UV_PYTHON_DOWNLOADS=never uv run --frozen --no-sync ruff check . | Lint passes | Git Bash outside sandbox launched; uv cannot find Python 3.13; Ruff never executed | Blocked |
| EVID-002 | UV_OFFLINE=true UV_PYTHON_DOWNLOADS=never uv run --frozen --no-sync ruff format --check . | Formatting passes | Same missing-interpreter error; formatter never executed | Blocked |
| EVID-003 | UV_OFFLINE=true UV_PYTHON_DOWNLOADS=never uv run --frozen --no-sync mypy src | Types pass | Same missing-interpreter error; mypy never executed | Blocked |
| EVID-004 | git diff --check | Clean whitespace | Exit 0 on 2026-09-29 | Pass |
| EVID-005 | uv run --frozen pytest; planned scenarios | Acceptance evidence | Excluded from coding assignment | Pending |
| EVID-006 | Startup, Inspector and relevant synthetic checks | Actual behavior verified | Excluded from coding assignment | Pending |

## 8. Implementation and review record

On 2026-09-29 the automatic workflow explicitly assigned this reviewed task to the coding
skill. Reconciled AGENTS.md, CONTRIBUTING.md, development, testing roadmap, SECURITY.md, architecture and configuration guidance. Current read tools remain read-only; future writes/testing authorization and independent prerequisite boundaries are explicit.
Original planning history below is retained as historical evidence, not current coding status.
No dependencies/tests/fixtures/secrets changed; synthetic writer setup remains pending.
Initial sandbox Bash attempts failed with CreateFileMapping Win32 error 5. Authorized escalation
allowed Bash to launch; all three actual uv checks then failed because Python 3.13 is absent.
Only Python 3.10 was found on PATH; no project .venv executables exist. No downloads or installs
were attempted. Thus no pass or introduced/pre-existing source failure attribution is possible.
Diff inspection preserves router/service/port/gateway boundaries and stable current catalog.
Review was task-plan self-review only. Tests, startup, Inspector/live calls and builds not run.
Documentation edits finished; shared prerequisite is not complete because the mandatory testing foundation is excluded. DOC-001/002 checked by document diff inspection only; feature acceptance is not claimed.

Planning only. Review readiness is recorded separately in [review](review.md); it does not
establish code correctness or acceptance. No code/test execution evidence exists at planning.
Preserve this plan and its scenario IDs when handing off testing. Packaging acceptance, if
dependencies change, requires a later build; do not use builds as runtime verification here.

## 9. Completion and handoff

- [x] Assigned independent coding behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed.
- [x] Documentation reflects final implemented behavior.
- [x] No unresolved decision changes assigned independent coding behavior.
- [x] Final diff reviewed and task record synchronized.

Final status: blocked for static environment and outstanding acceptance; independent coding finished.
Next action: Provide Python 3.13 and installed static tools, rerun EVID-001/002/003; separately
assign issues-001-testing-baseline.
