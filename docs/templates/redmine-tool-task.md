# <TASK-ID>: <Capability title>

Copy this template to `docs/plans/tasks/<task-id>.md` and follow
`docs/workflows/redmine-tools.md`. Paths are repository-relative. Start with the client's
outcome and the existing MCP catalog; use Redmine REST evidence to resolve implementation
details, not to generate one task per endpoint. Replace placeholders as each
phase completes; use `N/A - <reason>` for irrelevant fields. Do not leave contract decisions as
`TBD` when coding begins. Planned checks are not passing evidence. Keep evidence synthetic and
redacted. Add table rows as needed without renumbering existing requirements or criteria.

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | <Stable task ID; use a lowercase kebab-case filename> |
| Assigned capability | <Who calls the MCP tool and what outcome they need> |
| Type | <Extend existing tool / add tool / shared prerequisite> |
| Access | <Read / write; identify mixed behavior explicitly> |
| Destructive effects | <None, or exact destructive effects> |
| Status | <discovery / specified / planned / implementing / verifying / complete / blocked> |
| Dependencies | <Dashboard task IDs and completion evidence; include testing/access prerequisites> |
| Related tasks | <Links or N/A> |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | <Date and author/agent identifier> |
| Progress summary | <What is complete and what remains> |
| Next action | <Exact action another agent can take> |

## 2. Discovery and evidence

### Client outcome and repository baseline

- Client question or workflow this tool answers: <Concrete example>.
- Why an existing tool cannot already answer it, or which existing tool this extends: <Evidence>.
- Applicable instructions and policies: <Sources and relevant constraints>.
- Current tool names, defaults, schemas, and behavior: <Findings>.
- Relevant routers, services, ports, gateways, models, and bootstrap wiring: <Paths/symbols>.
- Working-tree baseline and unrelated changes to preserve: <Redacted summary>.
- Shared policy/testing prerequisite: <Completed task, or steps needed first>.
- Runtime permissions and synthetic reader/writer configuration: <Findings; no credentials>.

### Upstream evidence

| Source URL or versioned source | Date verified | Version supported | Endpoint/behavior | Permission required | Evidence or limitation |
|---|---|---|---|---|---|
| <Authoritative Redmine reference> | <YYYY-MM-DD> | <Version> | <Method/path> | <Permission> | <Finding> |

Differences between upstream API and current public contract: <Fields, defaults, errors, or
capabilities that need mapping; unsupported features and explicit compatibility handling>.

For a broad assignment, inventory requested MCP outcomes before dependent implementation:

| Client outcome / tool | Existing coverage | Read/write | Version support | Task ID | Dependencies | In scope/deferred |
|---|---|---|---|---|---|---|
| <Capability or N/A for an already scoped task> | <Tool> | <Access> | <Evidence> | <ID> | <IDs> | <Decision> |

### Questions and decisions

| ID | Question/assumption | Evidence or decision | Blocking? | Resolution date |
|---|---|---|---|---|
| DEC-001 | <Material uncertainty> | <Resolved decision and rationale> | <Yes/no> | <Date> |

## 3. Requirements

### Goal and boundaries

- Intended user and outcome: <Who calls the MCP tool, what question it answers, and why>.
- In scope: <Observable capabilities>.
- Out of scope: <Explicit boundaries>.
- Future enhancements: <Deferred behavior, separate from requirements>.
- Compatibility constraints: <Existing behavior and clients to preserve>.
- Permission/configuration prerequisites: <Required conditions>.

| ID | User need and intended outcome | Required observable behavior | Prerequisites/constraints |
|---|---|---|---|
| REQ-001 | <Need> | <Behavior> | <Constraint> |

Realistic synthetic examples: <Inputs and expected results, including an important edge case>.

## 4. Public contract and technical specification

### Tool and REST interface

| Area | Decision |
|---|---|
| Existing or new tool | <Name and rationale for extending versus adding> |
| Stable operation ID | <Exact ID> |
| Purpose and tool description | <Exact caller-facing description> |
| REST method and route | <Method/path> |
| Authentication and authorization | <Caller authentication and runtime access rules> |
| MCP exposure | <Explicit allowlist entry and behavior annotations> |

### Inputs

| Field/location | Type | Required/default | Validation | Omitted/null/empty behavior | Upstream mapping |
|---|---|---|---|---|---|
| <Field> | <Type> | <Rule> | <Constraint> | <Exact semantics> | <Query/body/path field> |

### Outputs and mapping

- Response model and field semantics: <Exact shape and optional fields>.
- Synthetic request/response examples: <Valid JSON examples>.
- Pagination, ordering, and expansions: <Defaults, bounds, and upstream limitations or N/A>.
- Upstream method, endpoint, query/body, and response mapping: <Exact transformation>.
- Upstream success status and body: <Including no-body success where relevant>.
- Public success status and MCP result: <Caller-visible behavior>.
- Compatibility: <Preserved defaults/names/shapes and intentional changes>.

### Errors

| Scenario | Detection layer | REST status and safe error | MCP result | Retry/reconciliation behavior |
|---|---|---|---|---|
| Invalid caller input | <Layer> | <Contract> | <Envelope> | <Behavior> |
| Missing/invalid authentication | <Layer> | <Contract> | <Envelope> | <Behavior> |
| Upstream credential rejected | <Layer> | <Contract> | <Envelope> | <Behavior> |
| Forbidden or missing resource | <Layer> | <Contract> | <Envelope> | <Behavior> |
| Upstream validation failure | <Layer> | <Contract> | <Envelope> | <Behavior> |
| Timeout or transport failure | <Layer> | <Contract> | <Envelope> | <Behavior> |
| Malformed/unexpected upstream response | <Layer> | <Contract> | <Envelope> | <Behavior> |
| Other unsuccessful upstream status | <Layer> | <Contract> | <Envelope> | <Behavior> |

### Write semantics

For read-only tasks, mark this section `N/A - read-only` and explain any relevant external effects.

- Exact side effects and destructive effects: <Changes to Redmine state>.
- Required permissions and runtime access configuration: <Least privilege; existing reader behavior>.
- Duplicate invocation and retry policy: <Evidence-backed behavior; no assumed idempotency>.
- Unknown outcome after timeout: <Caller-visible uncertainty and safe reconciliation>.
- Partial success/read-back failure: <Behavior; distinguish successful write from failed verification>.
- Concurrent updates: <Upstream guarantee or explicit limitation>.
- Disposable synthetic data: <Creation/identification and isolated writer prerequisites>.
- State verification: <How actual changes and permission boundaries will be observed>.
- Cleanup: <Only task-owned resources; failure handling and any non-reversible effects>.

Specification exit check: <No unresolved public-contract decisions; all applicable fields resolved>.

## 5. Implementation plan

| Step | Concrete change | Files/components | Depends on | Verification |
|---|---|---|---|---|
| 1 | <Shared policy/testing/access prerequisites> | <Paths> | <Task IDs> | <Check> |
| 2 | <Models and Protocol interfaces> | <Paths> | <Steps> | <Check> |
| 3 | <Redmine gateway and response/error mapping> | <Paths> | <Steps> | <Check> |
| 4 | <Service behavior> | <Paths> | <Steps> | <Check> |
| 5 | <REST validation and dependency wiring> | <Paths> | <Steps> | <Check> |
| 6 | <MCP registration and metadata> | <Paths> | <Steps> | <Check> |
| 7 | <Automated tests and fixtures> | <Paths> | <Steps> | <Check> |
| 8 | <Documentation and manual verification> | <Paths> | <Steps> | <Check> |

Dependency/configuration changes: <Exact planned changes or N/A; include lockfile handling>.

## 6. Acceptance criteria and traceability

| Criterion ID | Given | When | Then |
|---|---|---|---|
| AC-001 | <Observable precondition> | <Action> | <Observable result> |

| Requirement | Acceptance criterion | Verification method | Evidence | Result |
|---|---|---|---|---|
| REQ-001 | AC-001 | <Automated/manual scenario ID> | <Test/report reference; pending until run> | <Pending/pass/fail/blocked> |

Cover success, validation, permission boundaries, compatibility, and relevant upstream failures.
Each requirement needs evidence. For writes, acceptance must cover the response and resulting
Redmine state, not only the outgoing request. Link multiple scenarios where needed.

## 7. Test plan and execution record

### Scenario plan

Use pytest/pytest-asyncio, HTTPX MockTransport, ASGI transport with explicit lifespan, and MCP SDK
client checks as specified in the workflow. Default tests are offline with fake settings and no
Docker or real credentials. Live checks are opt-in and use the marked synthetic environment.

| Scenario ID | Acceptance criteria | Layer/method | Setup and input | Expected result | Offline/live |
|---|---|---|---|---|---|
| TEST-001 | AC-001 | <Unit/adapter/REST/MCP/Inspector> | <Synthetic setup> | <Assertion> | <Mode> |

Select relevant coverage and record scenario IDs or justified `N/A`:

- Defaults, filters, encoding, pagination, optional fields: <Scenarios>.
- Invalid inputs rejected before upstream access: <Scenarios>.
- Exact upstream query/body and response mapping: <Scenarios>.
- Successful, empty, malformed, and unsuccessful responses: <Scenarios>.
- Missing authentication and insufficient permissions: <Scenarios>.
- Existing tool names, contracts, and unrelated behavior preserved: <Scenarios>.
- MCP discovery, invocation, annotations, and error envelopes: <Scenarios>.
- Write payloads, no-body success, duplicate calls, and uncertain outcomes: <Scenarios or N/A>.
- Startup, live permission/state verification, and cleanup: <Scenarios and prerequisites>.

### Execution evidence

| Evidence ID | Command/procedure and environment | Scenario/check | Expected | Actual redacted result | Status | Date |
|---|---|---|---|---|---|---|
| EVID-001 | <Exact Bash command or Inspector procedure> | <IDs> | <Expected> | <Not run until executed> | <Pending/pass/fail/blocked> | <Date> |

Record repository checks (`bash scripts/check.sh`), offline tests (`uv run --frozen pytest` after
the baseline exists), and required startup/Inspector checks. Record a build when packaging or
dependencies change. Include relevant versions and distinguish mocks from live Redmine evidence.

Verification limitations and missing prerequisites: <Details; no unrun check marked passing>.

## 8. Implementation and review record

For a coding-only assignment, record static checks separately from testing. Leave test execution,
startup, Inspector, and live verification pending; list exact scenario IDs and prerequisites for
the later testing assignment. Do not modify the test plan or mark acceptance passed to compensate
for excluded verification.

- Changes made: <Behavior and affected components>.
- Plan deviations and reasons: <Decisions; update earlier sections if contracts changed>.
- Quality and automated test results: <Evidence IDs>.
- Startup and Inspector results: <Evidence IDs>.
- Documentation updated: <Tool reference, configuration, guides, changelog as applicable>.
- Final diff review: <Architecture, compatibility, logging, secrets, and unrelated changes>.
- Pre-existing failures versus introduced failures: <Distinguish explicitly>.
- Remaining defects/blockers: <Details or none>.

## 9. Completion and handoff

- [ ] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed; writes checked against resulting Redmine state.
- [ ] Documentation reflects the final behavior.
- [ ] No unresolved decision changes the specified behavior.
- [ ] Final diff reviewed and task record synchronized.

Final status: <complete / blocked / current in-progress phase>.

Outcome: <What changed and caller-visible effects>.

For coding-only work with all code changes finished, report **implementation finished; testing
pending** and use status `blocked` for outstanding acceptance work. Passing static checks does not
satisfy runtime acceptance. Check only the completion items supported by actual evidence.

If implemented but verification is unavailable, report **implemented, verification blocked** and
use status `blocked`, not `complete`.

Missing prerequisite or remaining work: <Exact blocker or none>.

Next action: <Concrete command/procedure or decision needed; none only when complete>.
