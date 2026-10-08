# Issue tags through existing REST

The Redmine server may only be queried using its existing REST API. No plugin installation,
server code/configuration change or restart is permitted. The earlier companion approach was
removed; nothing was installed on Redmine by this task.

## Current behavior

MCP `get_issue` keeps its existing upstream request, `GET /issues/{id}.json`, using the requesting
user's key and existing includes, visibility and read budgets. No supplemental endpoint or
Tags configuration flag is required. `IssueDetailWithTags` adds a nullable read-only field to
the detail response; list rows and writer observations retain their existing schemas.

If the existing response has `issue.tags` as a string array, its names are preserved and sorted
ordinally. Blank names, duplicates and non-string values fail strict upstream validation.
Examples of the mapped field:

```json
{"tags":["backend","urgent"]}
```

`[]` means the response reports no assignments. Missing tags become null with a `/tags`
`not_returned` observation. Explicit null remains unavailable. Neither unavailable case proves
an empty assignment set or a permission denial. Existing HTTP/transport/budget errors retain
their mappings, and malformed tags produce 502 `upstream_response`.

## User-supplied REST evidence (2026-10-08)

The user supplied the following request/response results in the conversation. These are manual
observations supplied by the user, not agent-executed tests or full MCP acceptance. Record only
IDs, counts and field presence; private descriptions and credentials are not retained here.

| Evidence ID | Request / condition | Supplied result | Conclusion / limit |
|---|---|---|---|
| TAGS-REST-001 | Project issue JSON list, structured `issue_tags = notification` plus open status | IDs 489 and 488, total_count 2, offset 0, limit 25 | Positive native tag-filter example; no tag array in the issues |
| TAGS-REST-002 | Same query with a nonexistent-name control | Empty issues, total_count 0, offset 0, limit 25 | Combined with TAGS-REST-001, establishes filtering by a known tag on this server |
| TAGS-REST-003 | `GET /issues/489.json` | Issue 489, no tags/tag_list/issue_tags field | Detail does not expose its complete assigned tags |

Exact tested structured parameters, before URL encoding:

```text
set_filter=1
fields[]=issue_tags
operators[issue_tags]==
values[issue_tags][]=notification
fields[]=status_id
operators[status_id]=o
values[status_id][]=
```

The user's project URL is `/projects/mcp-demo-child/issues`; changing its format to `.json`
uses the same native query controller. For MCP's existing numeric project interface, use
`issues.json` with top-level `project_id=<resolved ID>` and the structured filters. Multi-tag
ANY overlap, exact project/subproject boundaries, private-role behavior, continuation pages,
special-character names and mutation permissions have not been established by these samples.

## Query mapping from versioned source

Core `IssuesController#index:45-62` builds one `IssueQuery` for both HTML and API formats.
`Query#build_from_params:450-457` accepts `fields/operators/values`, or aliases `f/op/v`.
When `fields[]` is present, it clears the filters and uses that structured branch, so other
short filters must also be translated instead of being mixed in and silently lost.
Project context, include, limit, offset and sort remain top-level controls.

Tags 2.2.0 `issue_query_patch.rb:29-52` applies `issue_tags`, operator `=`, with `any: true`.
Multiple values are separate `values[issue_tags][]` entries. `IssueQuery#base_scope`,
`issue_count` and `issues:375-420` apply native visibility and filtering before count/paging.
The source supplies ANY semantics; the user samples establish single-name filtering only.

Gem 1.1.12 `tags_condition:309-311` uses SQL LIKE. `%`, `_` and backslash need explicit handling
before exposing literal tag-name filters; they must not silently become wildcard patterns.
Core short filters split values on `|`, which is another reason to use structured arrays.
TOOL-036 implements these mappings using repeated arrays and complete structured core filters.
Tag filtering is always available without an environment switch, as requested by the user.
It rejects wildcard/escape characters in this initial literal-name contract and relies on the
established native support. No Redmine changes or automatic probes occur. Runtime acceptance
is pending.

## Availability limitation

Issue assignment writes and creation of tag names were removed from the roadmap at the user's
request on 2026-10-08. Tags 2.2.0 source defines `edit_tags` and `create_tags`, but the inspected
REST contract does not establish effective permission preflight or concurrent assignment
preservation. No MCP tag writer is implemented. Known-name filtering remains supported.

The inspected Redmine 7.0.2 serializer and Tags 2.2.0 Light package do not expose tags in native
issue detail JSON. Therefore this mapper alone cannot supply tags on that native API. It can
preserve them if an existing response supplies a compatible field. The user-supplied detail
and list responses omit tags, confirming the limitation for the demonstrated requests.

Do not include API keys, credentials or private issue text in further evidence.
Undocumented endpoints, UI autocomplete and string parsing of a hypothetical `tag_list` are
not assumed. If the server exposes no REST tags field or supported read route, the requested
outcome is unavailable within the permitted access boundary.

## Source evidence

Checked 2026-10-08 without executing vendor code. Artifacts are kept in ignored `.local/vendor/`.

| Artifact | SHA-256 / provenance |
|---|---|
| User's Tags 2.2.0 Light ZIP | `242a7e348acd80544e89a0e461cfeb55c0ccfa85be1b9a1bfdb058dd6f875eae` |
| Repository-local Redmine 7.0.2 archive | `d45e6d4c373cc3c8d33f1f4d4a2ffae1e1adb18703160707467493de7b4be591` |
| Public [redmineup 1.1.12 gem](https://rubygems.org/gems/redmineup/versions/1.1.12), inspected without installation | `70804375f39021ff28ed0bfd68923a3a6f3d9a9a1bc180224996b319f644cf2c` |

Core `app/views/issues/show.api.rsb` has no tags field. Tags `config/routes.rb` and
`lib/redmineup_tags.rb` supply no issue-detail API serializer extension. Vendor `issue_patch.rb`
and the gem's taggable association show that tags exist internally; that does not grant REST
access or authorize direct database reads from MCP.

Known-name filtering is feasible independently of reading complete tags or listing vocabulary.
Never populate a returned issue's `tags` array using the selected filter names: an ANY match
does not prove every requested name matches, or that no other assignments exist.

At the original coding handoff, PREP-028 and TOOL-036 acceptance were pending and no agent tests,
startup, Inspector or live calls had run. The user subsequently assigned TOOL-036 testing:
82 focused offline checks and 3 selected live checks on localhost:3000 / Redmine 6.0.5 pass,
as does Inspector discovery/two calls. See [testing evidence](../testing/evidence/tool-036-tag-filter-testing.md).
Full 7.0.2, real overlap/private-role acceptance and PREP-028 mapper acceptance remain pending.
No deployment, server changes, plugin installation or fixture mutation occurred.
