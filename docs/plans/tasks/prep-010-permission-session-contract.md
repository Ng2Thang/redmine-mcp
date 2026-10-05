# prep-010-permission-session-contract: Resolve permission and session contracts

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-010-permission-session-contract |
| Assigned capability | Establish an implementable contract for personal-key permissions and caller isolation |
| Type / access / destructive effects | Shared evidence prerequisite / read-only source inspection / None |
| Status | complete |
| Dependencies | Existing prep-003, prep-005, prep-007 implementations; their pending runtime evidence is preserved |
| Related tasks | [Roadmap](../multi-user-writer-authorization.md); [dashboard](../index.md); prep-011 through prep-014 |
| Target Redmine version | 7.0.2; FastAPI-MCP 0.4.0; locked MCP SDK 1.30.0 |
| Last updated | 2026-10-05, Codex |
| Progress summary | All eleven permission/context branches and locked adapter/session integration reviewed in the dated contract report |
| Next action | Implement prep-011, then prep-012/013 using the resolved contract |

## 2. Discovery and evidence

Client outcome: each personal key receives the correct authorization context and cannot reuse
another caller's MCP session. Current identity is user-ID-only; catalog generation is global.
Read the [roadmap evidence](../multi-user-writer-authorization.md#baseline-evidence-and-limitations),
[tool reference](../../tool-reference.md), and existing write tasks tool-020 through tool-030.
The verified archive SHA-256 and official source URL are recorded in the roadmap.
All findings were checked on 2026-10-05; target runtime is unverified.

| Source | Finding | Remaining work |
|---|---|---|
| 7.0.2 roles controller/view/model | API permissions omit tracker restrictions | Classify necessary conditions separately from final authority |
| 7.0.2 users controller/view, user/project models | Visible memberships, own admin flag, built-in overrides, project/module gates | Record trustworthy positive/negative evidence for each context |
| Installed FastAPI-MCP `server.py` and repository `mcp/registration.py` | Shared tool list; request context used for invocation; stateful manager | Identify exact handler and transport hooks for request-local discovery and session binding |
| Existing write tasks | Different permission expressions and state effects | Produce one operation/context matrix covering all eleven existing writes |

Working tree was clean before planning. Preserve historical task status and unrelated edits.
Applicable instructions: repository AGENTS.md, English Markdown, Bash commands, no unrequested
tests. The conversation already provides the analysis; a new analysis skill pass is unnecessary.

Decisions: do not add a role-list or permission MCP tool; do not implement a Redmine plugin or
use an administrator key. A partial API remains partial, rather than being labelled definitive.

## 3. Requirements

| ID | Required observable behavior |
|---|---|
| REQ-001 | Every existing write has a documented context resolver and necessary permission expression |
| REQ-002 | Permission evidence differentiates denied, conditional, and unknown without inventing authority |
| REQ-003 | Locked MCP adapter has an exact request-context and session identity integration contract |
| REQ-004 | Downstream tasks have explicit error, compatibility, and verification contracts |

In scope: source inspection and task revisions. Out of scope: runtime code, dependency upgrades,
test implementation/execution, startup, live API calls, and data mutations.

## 4. Public contract and technical specification

MCP/REST operation, inputs, responses, pagination, and mutation semantics: N/A - evidence task.
Its outputs are an operation/context matrix and adapter design inside prep-012/013, not an API.
Record exact source files, relevant symbols, checked date, target version, and limitations.

The matrix must cover upload without project, file creation, attachment edit/delete containers,
issue creation/native copy, issue fields versus notes-only updates, own/other journal notes,
relation creation/deletion, and watcher addition/removal. Reuse existing route and payload contracts.
Resolve error behavior without hiding transport/malformed data as a permission denial.

The adapter design must specify request-context lifetime, credential forwarding, authentication
of every HTTP request, binding of POST/GET/DELETE session requests, session cleanup, and a
changed user/key presented with an existing session ID. Credentials are not tool arguments.
Identify the installed SDK callback API and guarded version-specific integration; do not patch
site-packages. If no safe integration exists, record the smallest dependency/lockfile change or
transport alternative as a blocked decision for review before coding.

Specification exit: this evidence task is decision-complete; downstream coding cannot start
from unresolved callback, effective-permission, or resource-context contracts.

## 5. Implementation plan

1. Read the verified 7.0.2 archive and existing tasks; record exact permission branches.
2. Inspect installed locked MCP sources for context propagation and session creation/lookup.
3. Write the resolved matrix into prep-012 and the adapter design into prep-013.
4. Confirm prep-011 session binding references the resolved design and does not require discovery.
5. Synchronize the roadmap/dashboard; leave unresolved contracts blocked with exact next actions.

No dependencies, environment, runtime, or test files are changed by this task.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Observable result | Method |
|---|---|---|---|
| AC-001 | REQ-001 | Eleven write operations each have context, permission expression, and target source | CONTRACT-001 source review |
| AC-002 | REQ-002 | Tracker, workflow, own-resource, admin, and non-member gaps have explicit handling | CONTRACT-002 contract review |
| AC-003 | REQ-003 | Named adapter/SDK symbols and session binding lifecycle are implementable | CONTRACT-003 source review |
| AC-004 | REQ-004 | prep-011/012/013 contracts match roadmap and preserve existing operation IDs | CONTRACT-004 document review |

All four source/document criteria pass in the [dated contract review](../prep-010-contract-review.md).
No runtime acceptance is claimed by this evidence-only task.

## 7. Test plan and execution record

N/A - no unit tests or runtime verification belong to this evidence-only task.
CONTRACT-001 through CONTRACT-004 are document/source reviews, not automated tests.
Later offline, REST/MCP, and opt-in state scenarios are owned by prep-014.

| Evidence ID | Procedure | Actual | Status |
|---|---|---|---|
| EVID-001 | Read verified 7.0.2 archive and installed FastAPI-MCP/SDK source; review AC-001 through AC-004 | Eleven operation expressions, partial metadata rules, safe list handler and SDK session owner binding resolved; 2026-10-05 | Pass |

Limitation: no target runtime, session attack, or state behavior has been observed.

## 8. Implementation and review record

Source/document review completed on 2026-10-05 in the dated contract report. Downstream
specifications now incorporate its exact integration and evidence rules. Initial 403 session
mismatch was revised to SDK 404 to preserve unknown-session nondisclosure. Doctor passed through
Git Bash outside the Windows sandbox. No runtime code, tests, or live checks in this task.

## 9. Completion and handoff

- [x] All eleven operation/context contracts resolved.
- [x] Session binding and discovery integration resolved.
- [x] Downstream tasks and dashboard synchronized from reviewed findings.
- [x] Final source/document review has passing evidence.

Final status: complete. Next action: implement prep-011 under the explicit prep-010 through
prep-014 assignment. Target runtime evidence remains owned by prep-014.
