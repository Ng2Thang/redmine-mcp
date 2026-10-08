# prep-028-redmineup-tags-api-readiness: Record REST Tags readiness and truthful detail output

## 1. Task identity and status

| Field | Value |
|---|---|
| Task ID | prep-028-redmineup-tags-api-readiness |
| Assigned capability | Record supported REST tag filtering and unavailable full-tag reads; preserve honest `get_issue` field mapping |
| Type / access / destructive effects | Extend detail read output / read-only / none |
| Status | blocked |
| Dependencies | Existing caller-key REST issue reader; user-supplied evidence now recorded |
| Related tasks | [filter issues](tool-036-filter-issues-by-tags.md), [dashboard](../index.md) |
| Target | User's existing Redmine 7.0.2 with Tags 2.2.0 Light; server changes prohibited |
| Last updated | 2026-10-08, Codex |
| Progress summary | REST-only implementation finished; mapper testing pending; full tags unavailable in demonstrated API |
| Next action | Separately authorize PREP-028-001..006 verification; TOOL-036 testing is independent |

## 2. Discovery and evidence

The user clarified that the Redmine server may only be queried through its existing REST API.
No plugin installation, controller deployment, configuration change, restart or other server
modification is allowed. The earlier companion implementation misunderstood this boundary and
has been removed. No companion was installed and no live environment was changed by the agent.

English Markdown, Git Bash commands, existing router/service/port/gateway architecture and
the implementation skill apply. No tests, test fixtures, startup, Inspector or live API calls
are authorized in this coding stage. Preserve the staged planning baseline and unrelated edits.

Exact core/vendor source was inspected without execution; ignored source files are evidence,
not deployable task output. See [integration evidence](../../integrations/redmineup-tags.md).
The inspected core `show.api.rsb` and Tags 2.2.0 Light do not expose issue tags in native detail
JSON. Plugin installation alone does not establish REST support. An existing server could
already have an API extension, but that requires actual response evidence rather than a guessed
endpoint. The source finding is not a live query of the user's server.

The user has now supplied native list/detail and positive/negative tag-filter responses.
[TAGS-REST-001..003](../../integrations/redmineup-tags.md) establish known-name filtering on
the demonstrated server and omission of full assigned tags from list/detail. Single-name
native filtering is user-observed; multi-name ANY and paging are source-backed, not yet accepted
through MCP. The agent did not execute these requests. The filter evidence is available to
TOOL-036 without waiting for PREP-028's detail-mapper acceptance or full-tag reads/discovery.

> **Filtering by tag name works through the existing REST API, even though the response
> does not contain the list of assigned tags.** This is user-supplied native API evidence,
> not acceptance evidence for an implemented MCP tag filter.

| Decision | Resolution |
|---|---|
| DEC-001 | Preserve existing target; do not alter the server |
| DEC-002 | Runtime scope remains one issue's existing REST detail; readiness also records known-name filtering; no assignment mutation |
| DEC-003 | Use only `GET /issues/{id}.json`; remove companion and supplementary GET |
| DEC-004 | Preserve returned string-array names; do not parse undocumented aliases or delimiters |
| DEC-005 | Existing native REST issue visibility and caller credentials govern the read |
| DEC-006 | No Tags feature flag, new endpoint or custom unavailable error is needed |
| DEC-007 | Existing REST tag filtering works; full assignment reads/catalogue/write preflight are separate capabilities |
| DEC-008 | TOOL-036 does not depend on full-assignment reads, tag discovery or complete tag serialization |

## 3. Requirements

| ID | Observable deliverable |
|---|---|
| REQ-001 | Respect REST-only access and disclose native source/API limitations |
| REQ-002 | Preserve `issue.tags` if returned; distinguish empty, null and omitted fields |
| REQ-003 | Use the existing caller key and issue visibility without broader access |
| REQ-004 | Strict response validation; no mutations or invented empty tags |
| REQ-005 | Preserve includes, budgets, list/writer schemas and operation IDs |

The full user outcome remains blocked if the existing server does not return tags. Preparing
the mapper does not make an absent REST field available.
That limitation does not block implementing the separate, source-backed tag-filter operation.

## 4. Public contract and technical specification

Existing `get_issue`, `GET /api/v1/issues/{issue_id}`: unchanged inputs/operation ID.
One existing upstream detail request: `GET /issues/{id}.json`, with unchanged include behavior.
No extra GET, HTML scraping, SQL access, admin credential, guessed endpoint or server plugin.

`IssueDetailWithTags` extends the baseline `IssueDetail` for this read response only. Its
`tags: list[str] | None` maps the existing JSON `issue.tags` field:

- Returned string array: preserve spelling/punctuation, validate nonblank unique strings,
  return ordinally sorted names.
- Returned `[]`: known empty assignment set.
- Missing field: null plus `/tags` `not_returned` visibility observation.
- Returned null: unavailable; do not turn it into `[]` or infer a permission denial.
- Malformed array/non-string/blank/duplicate names: existing 502 `upstream_response`.

Existing 401/403/404, transport/retry/deadline/byte/request errors retain their mappings.
List rows and create/update writer observations retain the baseline schemas. Tags do not
require an include expansion. No new configuration, dependency, migration or MCP operation.
If the real response uses another shape, establish that documented mapping separately using
sanitized evidence; do not assume `tag_list`, nested objects or autocomplete support.

## 5. Implementation plan

| Step | Deliverable |
|---|---|
| 1 | Correct the contract to prohibit server modifications |
| 2 | Remove authored companion source, extra GET adapter, flag, Compose/env entries and custom error |
| 3 | Keep detail-only field validation and native response mapping |
| 4 | Remove installation guidance and synchronize tool/task/dashboard docs |
| 5 | Run static checks; leave tests/live API access for a separately authorized stage |

## 6. Acceptance criteria and traceability

| Criterion | Requirement | Expected | Scenario |
|---|---|---|---|
| AC-001 | REQ-001 | No server artifacts or installation requirement; source limits recorded | PREP-028-001 |
| AC-002 | REQ-002 | Existing REST tags, empty, missing and null map truthfully | PREP-028-002 |
| AC-003 | REQ-003 | Existing same-key issue authorization/errors remain unchanged | PREP-028-003 |
| AC-004 | REQ-004 | Malformed tags fail; no writes/additional requests | PREP-028-004 |
| AC-005 | REQ-005 | Includes, operation, budgets and unrelated output schemas retained | PREP-028-005 |
| AC-006 | REQ-001..005 | Supplied REST evidence distinguishes supported filtering from absent full-tag data; MCP acceptance remains separate | PREP-028-006 |

## 7. Test plan and execution record

Testing is excluded. These scenarios are retained for a separately authorized handoff.

| Scenario | Later verification |
|---|---|
| PREP-028-001 | Source and removed-artifact review; no server-modification dependency |
| PREP-028-002 | Adapter/REST/MCP assigned, empty, absent, null and punctuated native tags |
| PREP-028-003 | Existing issue 401/403/404, ordinary/private-issue access with caller key |
| PREP-028-004 | Non-array/non-string/blank/duplicate tags, invalid IDs and client failures; exactly the existing GET and no mutations |
| PREP-028-005 | Default/empty/explicit includes; missing-field observations; unchanged list/writer schemas |
| PREP-028-006 | User list/detail and positive/negative filter samples recorded; later verify mapper/MCP parity without server changes |

Prior companion-era static checks were passing for their selected files, but do not verify
this REST-only revision. Tests, startup, Inspector and API calls have not been performed.
Current static results are recorded in section 8 after execution.

## 8. Implementation and review record

Removed the original authored Ruby companion files and Python supplementary adapter. Restored
baseline bootstrap, configuration, Compose/environment entries and error constants. Kept
`IssueDetailWithTags` so existing native tags can be observed without changing writer receipts.
The gateway uses only its existing native issue request and visibility mapper. Installation
instructions and the custom API contract were removed from public documentation.

The earlier companion and follow-up cleanup are superseded by this explicit REST-only constraint.
Deferred list/discovery/filter/write plans must not require changes to Redmine either.
The supplied controls now establish filter support; full reads, discovery and writes retain
their separate blockers. Staged task documents are preserved.

Static checks for this REST-only correction, executed through Git Bash with installed tools:

- `uv run --frozen --no-sync ruff check` scoped to the five remaining changed Python files:
  passed (`features/issues/models.py`, `ports.py`, `service.py`, `router.py`, and
  `integrations/redmine/issues.py`, relative to `src/redmine_mcp/`).
- `uv run --frozen --no-sync ruff format --check` on the same files: five already formatted.
- `uv run --frozen --no-sync mypy src`: passed, 124 source files.
- `git diff --check`: passed, with line-ending notices only.

Final source/configuration inventory found no companion endpoint, plugin directory, extra
adapter, Tags enable flag or custom unavailable constant. Bootstrap, config, constants,
Compose and env example have no remaining task diff. All generated companion directories
were removed only when empty; unrelated files and staged planning documents were preserved.
User response evidence has now been provided and recorded as TAGS-REST-001..003. No agent tests
or runtime verification were run. Earlier unrelated repository-wide static failures were not
rerun or changed.

### Roadmap review from supplied evidence (2026-10-08)

| Finding ID | Severity | Finding | Correction / resolution |
|---|---|---|---|
| TAGS-REV-001 | major | Plans conflated unavailable tag serialization with unavailable tag filtering | Separate capabilities; user controls establish native filtering; resolved |
| TAGS-REV-002 | major | Tag filtering depended on blocked full-name read/discovery output | Remove those dependencies; PREP-028 evidence is satisfied independently of mapper acceptance; resolved |
| TAGS-REV-003 | blocking | Structured tag query could silently drop existing short filters | Require complete structured translation in TOOL-036, repeated-value transport and unchanged top-level project/paging; resolved in specification |
| TAGS-REV-004 | blocking | Full tags and visible-name enumeration were treated as pending source access | Record actual missing fields and absence of a proven enumeration route; those outcomes were subsequently removed from the assigned roadmap |
| TAGS-REV-005 | historical; write scope removed | Read controls could be mistaken for write permission/atomicity proof | Source defines `edit_tags`/`create_tags`, but reads do not prove effective write authorization; the user subsequently removed the assignment-write task |
| TAGS-REV-006 | minor | Plans still requested already supplied REST responses | Link redacted user evidence and update next actions; resolved |

Current implementation review: detail reader consumes only the existing native JSON, observes
missing tags as null/not_returned and does not infer them from filters. List/writer schemas
remain unchanged. No runtime code changes were needed for that evidence update. The original
four tag outcomes were reviewed plans at that stage. Overall verdict then: TOOL-036 was planned for the
explicit bounded name contract; full reads/catalogue/writes remain blocked on their own gaps.

Documentation revision check: `git diff --check` passed with line-ending notices only.
No Python implementation changed in this revision; Ruff and mypy results above belong to
the earlier REST-only correction and were not rerun. No tests or live calls were performed.

### Assigned implementation follow-up (2026-10-08)

The assigned PREP-028 implementation was checked against its current contract. Retained the
existing strict detail-only tag model, native request and visibility mapping. Exported
`IssueDetailWithTags` from the issues feature package and used that public export in the
gateway, consistent with its existing feature imports. No new upstream request, input,
configuration, dependency, server artifact or MCP operation was introduced. Existing list
rows and writer receipt models retain their contracts. Filtering remains a separate task;
full-assignment reads, discovery and assignment writes were subsequently removed from the roadmap.

Working-tree baseline included the six staged planning documents, their unstaged revisions,
existing PREP-028 runtime edits and related documentation. Those changes were preserved;
no tests, fixtures or unrelated runtime files were changed.

Fresh static checks through Git Bash with installed tools:

- `uv run --frozen --no-sync ruff check` on `features/issues/{__init__,models,ports,service,router}.py`
  and `integrations/redmine/issues.py` under `src/redmine_mcp/`: passed.
- `uv run --frozen --no-sync ruff format --check` on the same six files: already formatted.
- `uv run --frozen --no-sync mypy src`: passed, 124 source files.
- Runtime/deployment inventory: no removed companion, generic Tags flag, custom unavailable
  constant or supplementary endpoint reference found.
- `git diff --check`: passed, with line-ending notices only.

The scoped implementation is finished; testing is pending. No repository-wide Ruff pass is
claimed. Tests, startup, Inspector, builds and live calls were not run. Later verification
must cover PREP-028-001..006: offline adapter/REST/MCP mapping and errors, reader permissions,
request/include/budget compatibility, and existing-server missing-field behavior. Any live
verification requires separate authorization and must not install or modify Redmine.

## 9. Completion and handoff

- [x] Server-modification approach removed.
- [x] Native detail field mapping implemented.
- [x] Actual REST evidence recorded: known-name filtering works; demonstrated detail/list omit full tags.
- [x] Current scoped static results recorded.
- [ ] Required tests/runtime acceptance recorded.
- [x] Documentation corrected to REST-only access.

Final status: **blocked** for mapper acceptance and the separate full-tag availability limit.
**Implementation finished; testing pending.** Truthful detail mapping is implemented;
filter-readiness evidence is available for TOOL-036.
The demonstrated API does not return full tags. No server modification or installation is
needed or permitted. Next action: separately authorize PREP-028-001..006 mapper verification.
TOOL-036 implementation is finished; its pending testing can be assigned independently.
