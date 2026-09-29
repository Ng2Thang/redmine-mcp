# Issues requirement analysis

## Scope and evidence

Full analysis of `docs/rest_api_redmine/issues.md`, sections Endpoint Summary, 1-7,
Resource Model Summary, and Related Redmine REST Resources, on 2026-09-29.
Source SHA256: `C3CB6636CFB8E5E548D934ACC790BE87B8FAFF562DB5A270A5977832BD9EB382`.
Baseline HEAD: `3013f7876506a57fcc8461c8cd74fc4158ea774a`; pre-existing changes in
`.codex/agents/redmine_feature_agent.toml` and `docs/workflows/redmine-tools.md` are preserved.
`deploy/compose.test.yaml` pins `redmine:6.0.5-bookworm`.

Inspected issues models, router, service, ports, Redmine issues/client/mapping adapters,
bootstrap, app lifespan, settings, API security/error handler, MCP registration, contributor,
architecture, configuration, development, security, tool reference, manual verification,
testing roadmap, workflow, task template, dependency metadata, and synthetic reader setup.

## Source requirements and current coverage

Paths below are repository-relative. Coverage is static, not runtime acceptance.

| Source ID | Source section/field | Documented behavior | Existing code evidence | Coverage | Gap or limitation |
|---|---|---|---|---|---|
| SRC-ISSUES-001 | 1: default/pagination | Read open issues; offset and limit | `features/issues/router.py:list_issues`, service and adapter; `common/pagination.py:Page` | implemented | Public default 25, bounds 1-100, offset >=0; no runtime verification |
| SRC-ISSUES-002 | 1: project/status/assignee | Numeric project, status ID/open/closed/*, assignee ID/me | `list_issues` in router, service, port, adapter | implemented | me is shared server account |
| SRC-ISSUES-003 | 1: issue_id/subproject/tracker/parent | Additional named ID filters, subproject !* | Router and `IssueReader` lack arguments | missing | Specify additive inputs |
| SRC-ISSUES-004 | 1: sort | Multi-column ascending/descending order | Adapter hardcodes id:asc | partial | Preserve default, expose optional sort |
| SRC-ISSUES-005 | 1: cf_x/other/date filters | Filterable custom fields and operators including created_on/updated_on | Router/port expose no extensible filters | missing | Upstream filter validity remains Redmine-owned |
| SRC-ISSUES-006 | 1: include | List attachments and relations; attachments since 3.4.0 | Adapter does not request list expansions; Issue has attachments but no relations | missing | Include schema and relation response needed |
| SRC-ISSUES-007 | 1/Resource Model: fields | Common references, subject/description, dates, progress, effort, custom fields, timestamps | `features/issues/models.py:Issue`, item/page mapping | partial | category/start_date/due_date/estimated_hours absent; fixed_version in resource summary absent |
| SRC-ISSUES-008 | 2: ID/show | Read visible issue by positive ID | router/service/port/adapter get_issue; MCP allowlist | implemented | JSON upstream; XML upstream is not a separate MCP feature |
| SRC-ISSUES-009 | 2: journals/attachments | Caller-selected detail expansions | Adapter always includes journals,attachments; Issue models these | partial | Preserve current omitted-input default; expose explicit include |
| SRC-ISSUES-010 | 2: children/relations/changesets/watchers | Other detail expansions; watchers since 2.3.0 | No inputs or response fields | missing | Visibility/permission restrictions remain upstream-owned |
| SRC-ISSUES-011 | 2: allowed_statuses | Workflow-aware statuses, since 5.0.x; tracker/status/role/subtask/blocking/parent constraints | No include input or field | missing | Forward upstream result, do not reproduce workflow logic |
| SRC-ISSUES-012 | 2: reactions | Issue and journal reactions since 7.1.0; visibility and feature enablement | No input/model support; target 6.0.5 | missing | Documented incompatibility; defer, do not upgrade target |
| SRC-ISSUES-013 | 3: create fields | Write issue envelope with project/subject and optional tracker/status/priority/description/category/fixed_version/assignee/parent/custom_fields/watchers/privacy/effort | Client only GET; no writer ports/routes | missing | Write-access and testing baseline prerequisites |
| SRC-ISSUES-014 | 3/4: attachments | Attach using upload/attachment flow | Metadata reads only | missing | Upload API is linked external resource; token-consumption contract needs evidence; no uploader in scope |
| SRC-ISSUES-015 | 4: editable attributes | Update issue envelope; project/tracker/status/subject and other editable attributes | No update path | missing | Other editable attributes is not an unlimited field list |
| SRC-ISSUES-016 | 4: notes/private_notes | Update journal comment with privacy flag | Read Journal only | missing | Private-note permission and workflow enforcement needed |
| SRC-ISSUES-017 | 5: delete | Destructive issue deletion | No DELETE client/route | missing | 6.0.5 controller deletes descendants; policy/least privilege/cleanup required |
| SRC-ISSUES-018 | 6: watcher add | Add user_id to issue watchers, since 2.3.0 | No write route or gateway | missing | Exact target permission/success semantics remain unverified |
| SRC-ISSUES-019 | 7: watcher remove | Remove issue watcher by user_id, since 2.3.0 | No write route or gateway | missing | Exact target permission/success semantics remain unverified |
| SRC-ISSUES-020 | Endpoint Summary/format | JSON and XML upstream representations | Client JSON only; REST/MCP typed JSON | partial | Retain JSON adapter; no XML client-facing format parameter planned |

## Version and permission constraints

Authoritative sources actually checked on 2026-09-29:

- [Redmine issues documentation](https://www.redmine.org/projects/redmine/wiki/Rest_Issues):
  live documentation is a comparison reference, not proof of support in 6.0.5.
- [6.0.5 issues controller](https://raw.githubusercontent.com/redmine/redmine/6.0.5/app/controllers/issues_controller.rb):
  create uses add_issues and returns 201 with show representation; update/delete use API success
  rendering; deletion processes descendants. API success renderer status still needs verification.
- [6.0.5 show serializer](https://raw.githubusercontent.com/redmine/redmine/6.0.5/app/views/issues/show.api.rsb):
  seven non-reaction expansions are present, including allowed_statuses. Watcher data requires
  view_issue_watchers; no reaction serialization is present.
- [6.0.5 issue model](https://raw.githubusercontent.com/redmine/redmine/6.0.5/app/models/issue.rb):
  visibility follows view_issues; editing depends on edit_issues or edit_own_issues; notes use
  add_issue_notes; deletion uses delete_issues. Field/workflow conditions still apply.

Attempts to fetch the target watcher controller, list serializer, and permission registry failed;
those specific claims remain unverified. Local source does not state precise least permissions,
success bodies, or authorization policy. Source minimums 2.3.0/3.4.0/5.0.x precede target;
reactions 7.1.0 is later. Successful source inspection does not establish configured permissions.

## Assumptions and unresolved questions

- Repository fact: current runtime has one shared reader credential and bearer token; no pytest
  baseline or separate writer configuration. Synthetic reader has view_issues only.
- Workflow fact: owner-approved future write/testing scope exists, but shared policy/testing
  prerequisite must precede dependent tool implementation. Coding skill explicitly excludes
  installing test dependencies, creating fixtures, and live verification.
- Owner decision on 2026-09-29: use a separate opt-in writer deployment with a restricted
  writer key/token; preserve default read-only deployments. The parent relayed this explicit
  choice during orchestration. Synthetic writer setup and permission evidence remain pending.
- No assumed upstream retries, idempotency, rollback, or transactional guarantees. Write status,
  watcher permission semantics, and upload token semantics require target evidence.
- Other filters are extensible query values, not permission to add linked resource APIs.

## Handoff

Existing read tools cover basic pagination/filters and fixed detail expansions. Plan cohesive list
and detail extensions, three issue mutation capabilities, and watcher membership operations.
Separate policy documentation, testing baseline, and write access prerequisites. Account for
unsupported reactions and external upload API explicitly. This report is analysis, not review.
