# Find my open issues

See issues assigned to your account and choose what to work on next.

You need a [connected reader](get-started.md) and access to the chosen project. Website and
project #10 below are synthetic examples.

## Find assigned issues

```text
Show my open issues in the Website project, grouped by priority.
Include each issue's ID, subject, status, and due date when available.
Tell me whether the list is complete or partial.
```

**How it works**

1. Confirm your identity with `get_current_user` if you have not checked the connection.
2. Resolve Website using `list_projects`; select the intended project if names are ambiguous.
3. Use `list_issues` with the returned project ID and caller filter:

```json
{"project_id": 10, "assigned_to_id": "me", "status_id": "open", "limit": 25, "offset": 0}
```

4. Check pagination policy before continuing; collect permitted pages before grouping results.

**Example result**

> High: #123 Fix login redirect, In progress, due 2026-10-16.
> Normal: #128 Update help text, New, no due date returned.
> Illustrative rows only; the actual answer should state its collection scope.

## Review a backlog or draft progress

- Use `status_id: "closed"` for closed issues or `status_id: "*"` for all statuses.
- Omit the project filter to start across visible projects; narrow if the query is too broad.
- Ask to exclude subprojects with `include_subprojects: false` and a project ID.

Grouping by priority happens in the client after retrieval. Supported tool sort values
concern issue ID and update time, not priority.

To review the project backlog, omit `assigned_to_id` or use a known user's numeric ID as
a string. Resolve category and Target version IDs through their project listing tools
before filtering. These are variations of the same issue-list workflow.

For a quick progress draft, try:

```text
Draft an update for Website from issues updated since 2026-10-05T00:00:00+07:00.
Include closed issues and issue IDs. Check visible notes for important changes,
state the collection scope, and do not post the draft anywhere.
```

The client can use `updated_since` and `status_id: "*"`, then read selected issues' journals.
This selects issues updated since the starting instant, with no upper bound; current status
does not prove when an issue was completed. State collection time and any missing context.

## Missing or incomplete issues

Check the account, project, and status. Issues assigned to someone else will not match
`"me"`. A large preview is not the whole backlog; refine supported filters. See
[missing results](troubleshooting.md#results-are-empty-or-incomplete).

**Related tools and next steps**

`get_current_user`, `list_projects`, `list_issues`. Continue with
[Understand an issue](issue-summary.md).
