# tool-013: Get the current user's profile and memberships

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | tool-013-get-current-user |
| Assigned capability | Let an MCP client identify its caller and inspect visible project memberships and roles. |
| Type / access / destructive effects | Add tool / read-only / none |
| Status | blocked - implementation finished; testing pending |
| Dependencies | prep-002 offline baseline complete; prep-003 identity foundation implemented with runtime acceptance pending |
| Related tasks | Existing issue assignee `me` behavior; no additional tool dependency |
| Target Redmine version | Redmine 7.0.2; runtime acceptance pending |
| Last updated | 2026-10-02, Codex |
| Progress summary | Approved contract implemented; lint, formatting, types, architecture, and diff checks pass; automated and runtime acceptance not executed. |
| Next action | Review prep-004's dated offline/live evidence and complete the remaining task-specific acceptance fixtures and clean live rerun. |

## 2. Discovery and evidence

The client needs to answer "Who am I in Redmine, and which visible projects have memberships
and roles for me?" Existing tools cannot return a profile. Authentication already calls
`users/current.json`, retaining only the ID; this tool preserves that lookup and separately
requests the profile with memberships. The upstream client is bound to the same normalized key.

Implementation uses the users router, service, Protocol, models, and Redmine gateway, composed
through bootstrap and API dependencies. Both the MCP catalog and application read-operation
policy explicitly register `get_current_user`. Existing read annotations are reused.

Applicable rules: AGENTS.md, docs/workflows/redmine-tools.md, the task template, and the approved
implementation plan. All Markdown is English; commands use Git Bash. Existing staged changes
in runtime constants, auth, mapping, API, catalog, architecture documentation, and changelog
were present before this assignment and must be preserved. No secrets were read or recorded.

| Source | Checked | Version | Evidence / permission |
|---|---|---|---|
| [Users API](https://www.redmine.org/projects/redmine/wiki/Rest_Users) | 2026-10-01 | General reference | Current-user lookup and memberships expansion; ordinary users can read their own profile. |
| Users controller (prior source inspection; current release review pending) | 2026-10-01 | prior sample | Show permits API authentication without the controller's admin gate; memberships are filtered by project visibility. |
| User serializer (prior source inspection; current release review pending) | 2026-10-01 | prior sample | Membership IDs, project references, roles, optional inherited flags; email can be omitted; API key must be excluded. |

Versioned source was read directly during planning; no live acceptance is implied. User profile
data is personal information, but returning the selected caller profile is explicitly authorized.

| Decision | Resolution |
|---|---|
| Output breadth | Owner selected basic profile plus memberships and roles. |
| Inputs | None; memberships always included. |
| Authentication reuse | Preserve ID-only auth and perform one additional profile read. |
| Verification scope | Static checks only in this coding stage; no test edits, unit tests, startup, or Inspector execution. |

## 3. Requirements

| ID | User need / required observable behavior |
|---|---|
| REQ-001 | Return the profile belonging to the caller's authenticated key, never another identity. |
| REQ-002 | Return visible memberships with project and role references; default absent inheritance to false. |
| REQ-003 | Expose nullable email with existing visibility observations and exclude credentials/extra metadata. |
| REQ-004 | Publish an authenticated read-only MCP tool and REST route with existing sanitized error behavior. |

Groups, arbitrary-user lookup, account metadata, pagination, effective permission computation,
and writes are out of scope. Existing names and contracts remain unchanged.
An ordinary reader with no returned memberships receives an empty array. Hidden email does
not fail the call and must not be inferred to mean no email exists.

## 4. Public contract and technical specification

| Area | Contract |
|---|---|
| Stable operation / MCP name | get_current_user |
| REST interface | GET /api/v1/users/current; HTTP 200 typed CurrentUser body |
| Inputs | No tool arguments; Inspector input `{}`; no caller-selected ID or expansion |
| Authentication | X-Redmine-API-Key, existing get_auth_context and require_read_access |
| Exposure | Explicit MCP catalog and read-operation policy; existing read-only, non-destructive, idempotent, open-world hints |
| Upstream | GET users/current.json with include=memberships, using the same caller key |
| Output | id, login, firstname, lastname, nullable mail, memberships, visibility |
| Membership | Positive integer id, project {positive integer id, nonempty name}, roles array |
| Role | Positive integer id, nonempty name, boolean inherited (default false when omitted) |

Profile IDs are strict positive integers; the response ID must equal the authenticated
principal. Login is a nonempty string; first and last name are required strings. No email-format
dependency is added. Missing email maps to null with `/mail` `not_returned`; explicit null
maps to null without an observation. Memberships, projects, and role arrays are required typed
data. An absent or malformed memberships array fails rather than becoming an empty list.
Upstream order and duplicate role entries are preserved; no deduplication or pagination is added.

Models ignore unknown fields at every level and the gateway selects public top-level fields.
Credentials, admin/status flags, timestamps, groups, and custom fields are not returned.
Memberships represent only what Redmine returned for the requesting user's project visibility.

Example input: `{}`. Example output for a profile without visible memberships:

```json
{"id":2,"login":"demo-reader","firstname":"Demo","lastname":"Reader","mail":null,"memberships":[],"visibility":{"scope":"requesting_redmine_user","observations":[{"path":"/mail","state":"not_returned"}]}}
```

| Scenario | Existing public behavior |
|---|---|
| Missing/invalid/rejected initial key | 401, sanitized authentication detail |
| Rejected key during profile read | 401 invalid_credentials |
| Upstream denial / absent resource | 403 access_denied / 404 resource_not_found |
| Missing user, mismatched ID, invalid field or membership shape | 502 upstream_response |
| Timeout / transport / oversized response | 504 upstream_timeout / 502 upstream_unavailable / 502 upstream_response_too_large |
| Other upstream/runtime failures | Existing shared client and error-handler mappings; no new error envelope |

MCP presents bodies through its existing tool-result envelope and failures through its existing
error handling. No automatic retry or key persistence is introduced. Write semantics: N/A,
read-only. No unresolved public-contract decision remains.

## 5. Implementation plan

1. Define CurrentUser, UserMembership, MembershipRole, UserReference, and the UserReader Protocol.
2. Implement the RedmineUsers gateway using shared resource identity and visible-item mapping.
3. Add UserService and the authenticated router, passing the principal ID internally.
4. Wire container/dependencies, register the router before MCP creation, and update both catalogs.
5. Update tool reference, manual scenarios, changelog, and dashboard.
6. Run allowed static checks and inspect the diff; hand off acceptance separately.

No dependency, configuration, lockfile, packaging, or test infrastructure change is needed.

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Expected result | Scenarios | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | Same normalized caller key and authenticated ID; mismatches rejected | USER-001, USER-007 | Pending |
| AC-002 | REQ-002 | Visible memberships and roles mapped, empty array valid, inheritance preserved/defaulted | USER-001 through USER-003 | Pending |
| AC-003 | REQ-003 | Correct nullable email observations; no extra metadata or credentials | USER-004, USER-005 | Pending |
| AC-004 | REQ-004 | Authorized discovery/invocation, read annotations, sanitized failures, prior tools preserved | USER-006, USER-008 through USER-010 | Pending |

## 7. Test plan and execution record

All scenarios below are planned, not executed. Do not write or run tests in this coding stage.
Later offline verification uses the existing pytest/pytest-asyncio baseline, HTTPX MockTransport,
ASGI transport with explicit lifespan, fake settings without dotenv, and MCP SDK client checks.

| Scenario | Setup and expected result | Method |
|---|---|---|
| USER-001 | Ordinary user; exact auth/profile calls use caller key, profile includes memberships, project and role IDs/names | Offline gateway/REST; synthetic Inspector |
| USER-002 | Returned memberships=[] succeeds; missing/null/object memberships, malformed membership/project/roles fail with sanitized 502 | Offline gateway |
| USER-003 | Missing inherited defaults false; true/false retained; non-boolean rejected; nested unknown fields excluded | Offline gateway |
| USER-004 | Missing email yields null plus observation; explicit null has no observation; returned string retained | Offline gateway |
| USER-005 | Upstream api_key and extra account metadata never appear in REST/MCP output or logs | Offline REST/MCP |
| USER-006 | Missing, repeated, malformed, or rejected initial key fails; profile key revoked after authentication uses existing error | Offline REST |
| USER-007 | Profile user ID differs from principal, is missing, boolean/string/nonpositive, or user envelope is invalid; sanitized 502 | Offline gateway/REST |
| USER-008 | Timeout, transport, 403/404/429/5xx, invalid JSON, oversized body; shared mappings and no retry | Offline gateway/REST |
| USER-009 | Tool appears exactly once, input has no user arguments, hints match catalog, invocation succeeds/errors properly; old operations preserved | Offline MCP; review existing fixed catalog assertions |
| USER-010 | Startup/shutdown and Inspector `{}` under two ordinary synthetic accounts; compare profile and visible memberships, empty membership account and inherited roles when fixtures exist | Marked synthetic environment |

Synthetic checks use an existing marked environment and private personal keys. Do not seed,
reset, restore, or mutate Redmine merely to verify this reader. If relevant fixture states are
unavailable, record the limitation and use offline cases without claiming live evidence.

| Evidence | Procedure | Result |
|---|---|---|
| EVID-001 | bash scripts/doctor.sh, 2026-10-01 | Passed; required Git Bash/Python/uv prerequisites available |
| EVID-002 | UV_NO_SYNC=1 bash scripts/check.sh, 2026-10-01 | Passed: Ruff lint, formatting (127 files), mypy (79 source files), architecture boundaries/cycles (79 modules). First run identified a new import-format issue, corrected before the passing run. |
| EVID-003 | git diff --check and final source diff review, 2026-10-01 | Passed; new source reviewed directly because untracked files are absent from git diff. Existing staged changes preserved. |
| EVID-004 | USER-001 through USER-009 | Not run; separate authorization required |
| EVID-005 | USER-010 and remaining prep-003 foundation acceptance | Not run; separate authorization required |

## 8. Implementation and review record

- Implemented the users feature, strict identity/reference validation, inherited-role defaults,
  nullable email observations, explicit public field mapping, route, composition, and catalogs.
- Updated public reference, Inspector guide, changelog, task, and dashboard.
- Created this task document as explicitly requested by the approved implementation plan.
  The skill's missing-task-file stop rule does not prevent the owner's authorized task creation.
- Preserved prior staged changes; no tests, dependencies, live state, or credential files changed.
- Static checks and final diff review pass (EVID-002/EVID-003). Automated/runtime acceptance
  remains pending; review tests with fixed catalog expectations for updates in the later stage.

## 9. Completion and handoff

- [x] Required behavior implemented.
- [ ] Every requirement has passing acceptance evidence.
- [ ] Relevant automated tests and repository checks pass.
- [ ] Required live verification completed.
- [x] Documentation reflects the implemented contract.
- [x] No unresolved decision changes specified behavior.
- [x] Final diff reviewed and task record synchronized with static outcomes.

Final status: blocked - implementation finished; testing pending.
Next action: separately authorize automated scenarios USER-001
through USER-009, catalog assertion updates, synthetic USER-010, and foundation acceptance.
No planned test is represented as passing.

## 10. Authorized prep-004 continuation: 2026-10-02

The full credential-free suite passes 356 tests; Ruff, formatting, mypy, architecture,
source/wheel build, and whitespace checks pass. The focused MCP startup race fix was
separately approved by the user and verified with readiness, concurrency, and cleanup cases.

USER-001 through USER-009 executed variants pass offline. The live ordinary profile's public fields, ten memberships, and roles match Redmine. USER-010 remains blocked by the missing second ordinary personal key and other account/role variants.

See [the dated verification ledger](../prep-004-verification.md) for procedures, exact
case mapping, and limitations. Current authentication is each caller's personal
`X-Redmine-API-Key`; visibility is `requesting_redmine_user`, and rejected keys return 401.
Future contract wording was reconciled; historical discovery/execution notes were retained.
Final current status remains **blocked** until outstanding acceptance is established; the
earlier handoff above describes the previous implementation stage.

## Prep-020 evidence reconciliation, 2026-10-07

Current `get_current_user` functional evidence is mapped in the
[32-operation ledger](../current-catalog-acceptance.md): 1086 offline and 21 owned 7.0.2 live
cases pass, including Inspector and cleanup. This preserves the preceding historical record;
it does not blanket close this owner's wider matrix. See H3 and the operation row for
matching criteria and exact remaining fixtures/role variants before claiming broader acceptance.
