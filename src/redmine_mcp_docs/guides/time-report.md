# Summarize logged time

Review hours credited to you over an explicit date range, grouped by project or day.

You need a [connected reader](get-started.md) and time-entry visibility.
Resolve "last week" or other relative dates
to exact dates in your timezone before collecting data.

## Report logged hours

```text
Summarize my logged time from 2026-10-05 through 2026-10-09, inclusive, by project.
Use time-entry dates, not issue dates. Collect permitted pages and deduplicate entries.
State whether totals are complete for the caller-visible scope or partial.
```

**How it works**

1. Confirm your account with `get_current_user` when needed.
2. Use `list_time_entries` with inclusive log-date filters:

```json
{"user_id": "me", "spent_from": "2026-10-05", "spent_to": "2026-10-09", "limit": 100, "offset": 0}
```

3. Check pagination policy before each continuation. Narrow scope if requested and disclose
   that the narrower query changes the report's scope.
4. After complete permitted collection, deduplicate by entry ID and sum `hours` with decimal
   arithmetic. Group by project ID, keeping names as display labels.

**Example result**

| Project | Hours |
| --- | --- |
| Website | 12.5 |
| Customer Support | 3.0 |

Values are invented. A real report should state dates, credited user, visibility scope,
and whether pagination completed. `total` counts entries, not hours.

## Adjust the report or log time

Add `project_id` for one project. Time-entry queries exclude subprojects by default;
use `include_subprojects: true` with a project ID if needed. Add `issue_id` for logs directly
on one issue, or group by `spent_on` for a daily breakdown.

To record time with an enabled writer, use an explicit issue, date, and positive hours:

```text
Log 1.5 hours on issue #123 for 2026-10-09 with comment "Investigated login redirect".
Show available activities first and create one entry after I choose an activity.
Show the entry ID and verification result.
```

This uses `list_project_time_entry_activities` and writer-only `create_time_entry`, credited
to your account. Native log-time permission is required; activity discovery needs time-entry
visibility. Creation acceptance testing is pending, and activity discovery testing was waived.
After an uncertain result, inspect existing logs before retrying; identical calls can create
duplicates. See [write guidance](write-actions.md) and the
[time-entry contract](../docs/tool-reference.md#create-a-time-entry).

## Missing or incomplete hours

Your account may only see its own logs. Empty results do not prove no other logs exist.
Do not add issue `spent_hours` or descendant-inclusive totals to entry sums; this can count
the same time twice. Stop on budget or scope errors and label totals partial or unavailable.
A preview cannot establish the full period's hours.

**Related tools and next steps**

`list_time_entries`, `list_issue_time_entries`, `get_current_user`, `list_projects`.
See the [reference guide](reference.md) for time-entry creation, correction, and deletion.
