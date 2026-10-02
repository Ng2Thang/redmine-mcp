# Redmine 7.0.2 files and issue capabilities

This plan supports Redmine 7.0.2. Document REST operations are outside its scope.
Document category enumeration remains available through the Enumerations API.

Checked: 2026-10-01. This is the master plan for the requested MCP capability set.
The [dashboard](index.md) is the execution ledger; child contracts live in
`tasks/<task-id>.md`. This plan assigns documentation and future implementation work.
It does not authorize running tests, modifying a Redmine instance, or deploying a writer.

## Outcome and boundaries

Preserve the eleven existing operations. Extend `list_issues` and `get_issue`;
plan fifteen additional operations: four readers and eleven writers within
the 7.0.2 API surface. The reader deployment
remains read-only. A separate, false-default writer deployment exposes only
explicitly approved write operations to restricted caller identities. Both use
the requesting user's personal Redmine API key; neither uses an administrator key
or `X-Redmine-Switch-User`.

The client constructs a schedule from visible issue dates, parent links, relations,
progress, and project versions. Redmine has no JSON REST Gantt resource; this
workflow is governed by `view_issues`, not `view_gantt`. It must be labeled a
client-rendered schedule and cannot claim exact native Gantt parity.

Issue deletion, administration, time logging, project/version management, generic
CRUD forwarding, browser scraping, and a Redmine plugin are outside this plan.
Attachment access follows its Project, Version, or Issue container. Document
attachments are excluded from this target. No `manage_files` shortcut may
authorize an Issue attachment.

## Version evidence and prerequisite

The [synthetic Compose deployment](../../deploy/compose.test.yaml) pins
`redmine:7.0.2-bookworm` by immutable index digest. The user waived actual runtime
verification on 2026-10-02; no runtime acceptance result is claimed.
The [Redmine REST index](https://www.redmine.org/projects/redmine/wiki/Rest_api)
does not establish Documents REST for this target. Document REST task drafts
are excluded from this roadmap.
`tool-016` remains in scope because
[Enumerations REST](https://www.redmine.org/projects/redmine/wiki/Rest_Enumerations)
documents the document category endpoint separately.
`prep-005-redmine-7-0-2` pins the target. The user accepted continuation without
runtime verification, so dependent coding uses exact 7.0.2 source evidence.

The following authoritative references are evidence, not permission to expand
the catalog: [Documents](https://www.redmine.org/projects/redmine/wiki/Rest_Documents),
[Files](https://www.redmine.org/projects/redmine/wiki/Rest_Files),
[Issues](https://www.redmine.org/projects/redmine/wiki/Rest_Issues),
[Relations](https://www.redmine.org/projects/redmine/wiki/Rest_IssueRelations),
[Journals](https://www.redmine.org/projects/redmine/wiki/Rest_Journals),
[Attachments](https://www.redmine.org/projects/redmine/wiki/Rest_Attachments),
and [enumerations](https://www.redmine.org/projects/redmine/wiki/Rest_Enumerations).
Copying through top-level `copy_from` is supported by the
[Issues controller source](https://github.com/redmine/redmine/blob/master/app/controllers/issues_controller.rb)
but is absent from the public Issues API reference; exact 7.0.2 source must verify it.

## Public tool ownership

| Existing operation extended | Owner | Change |
|---|---|---|
| `list_issues` | tool-014 | Optional `include` for attachments/relations; preserve existing defaults. |
| `get_issue` | tool-015 | Expose estimate and attachment URL context needed by later operations. |

| New reader | Owner | Upstream method and path |
|---|---|---|
| `list_document_categories` | tool-016 | GET /enumerations/document_categories.json |
| `list_project_files` | tool-017 | GET /projects/{project_id}/files.json |
| `get_attachment` | tool-018 | GET /attachments/{attachment_id}.json |
| `download_attachment` | tool-019 | GET metadata, then validated content URL |

| New writer | Owner | Upstream method and path |
|---|---|---|
| `upload_attachment` | tool-020 | POST /uploads.json?filename=... |
| `add_project_file` | tool-021 | POST /projects/{project_id}/files.json |
| `update_attachment` | tool-022 | PATCH /attachments/{attachment_id}.json |
| `delete_attachment` | tool-023 | DELETE /attachments/{attachment_id}.json |
| `create_issue` | tool-024 | POST /issues.json; optional top-level copy_from |
| `update_issue` | tool-025 | PUT /issues/{issue_id}.json |
| `update_issue_note` | tool-026 | PUT /journals/{journal_id}.json |
| `create_issue_relation` | tool-027 | POST /issues/{issue_id}/relations.json |
| `delete_issue_relation` | tool-028 | DELETE /relations/{relation_id}.json |
| `add_issue_watcher` | tool-029 | POST /issues/{issue_id}/watchers.json |
| `remove_issue_watcher` | tool-030 | DELETE /issues/{issue_id}/watchers/{user_id}.json |

`create_issue(copy_from=...)` requires source Copy issues
and destination Add issues. `update_issue(notes=...)` allows notes-only updates
without imposing Edit issues; field changes use Edit issues/Edit own issues.
Journal editing checks the journal author. Parent changes require Manage subtasks.
Privacy flags require the relevant public/private permission. Watcher and relation
mutations retain their independent permissions. These are separate authorization
cases inside consolidated tools, not separate tool names.

## Shared interface and side-effect rules

- Upstream JSON calls use `X-Redmine-API-Key`, `Accept: application/json`,
  and `Content-Type: application/json` for JSON writes. Uploads use raw bytes and
  `Content-Type: application/octet-stream`. Do not send API keys as query parameters.
- `upload_attachment` accepts base64 content, a filename, and at most 5 MiB of
  decoded data by default; return Redmine's upload token/ID. The limit is configurable
  and also applies to decoded downloads. No client filesystem paths or arbitrary URLs.
- `download_attachment` resolves metadata by ID, validates the content URL against
  the configured Redmine origin and base path, rejects redirects, and limits actual
  streamed bytes. Project/Version downloads may increment Redmine counters.
- Attachment writes require a declared container type (`project`, `version`,
  or `issue`) and positive container ID. Verify the attachment
  belongs to that container before mutation by reading the containing Project/
  Version file list or Issue and finding the attachment ID. The
  attachment metadata endpoint alone does not establish container identity.
  Support only these three container types.
- Reader pages retain existing `items,total,limit,offset,visibility` semantics
  where the upstream endpoint provides pagination. Files and enumerations return
  `items,visibility`; do not invent a total for the unpaged Files API.
- Update bodies contain only supplied fields; reject unknown fields and empty
  updates. Nullable clearing is explicit. Omitted privacy values remain unchanged.
- Write receipts distinguish upstream acceptance from matched, mismatched, or
  unavailable read-back. A failed read-back does not undo a successful write.
  A timeout after dispatch reports an unknown outcome. No automatic write retries,
  inferred atomicity, or rollback promises.
- Never log keys, bearer credentials, upload tokens, binary payloads, or full issue
  bodies. Return sanitized upstream errors and keep resource visibility scoped to
  the requesting Redmine identity.

The exact per-tool inputs, outputs, REST route, error mapping, and version evidence
are owned by the child task. If exact 7.0.2 evidence contradicts a draft contract,
record a reviewed contract change before coding that tool; do not silently adapt it.

## Strict execution order and quality gates

The active dashboard rows form one chain; deferred Document rows are excluded.
`prep-004` reconciles pending acceptance of the existing implementation;
`prep-005` establishes the pinned 7.0.2 environment; reader tasks follow;
`prep-007` introduces the writer boundary; `prep-008` prepares disposable
writer verification; writer tools follow; `prep-009` owns final release review.
No later independent work bypasses a blocked predecessor.

Each task passes specification review, coding/static checks, a separately
authorized testing stage, acceptance evidence, and explicit user acceptance.
The user's repository instruction forbids automatic unit-test verification.
Unless the user separately authorizes a task's tests, mark its implementation
finished but testing pending, set `blocked`, and stop the chain.
Approval of a task document or code does not grant testing permission.

Each tool task uses all nine sections of the
[task template](../templates/redmine-tool-task.md). Acceptance requires
meaningful offline REST/MCP and opt-in synthetic Inspector scenarios for
the changed behavior. Write tasks additionally verify resulting Redmine
state, permission variants, duplicate/timeout uncertainty, and cleanup.
Never label planned scenarios as passing evidence. User acceptance follows
the evidence report and precedes opening the next task.

See the [workflow](../workflows/redmine-tools.md) and
[tool reference](../tool-reference.md) for existing architecture and contracts.
