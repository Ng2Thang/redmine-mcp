# Use write actions

Write actions change Redmine records. Use them when you intend to create or update a
specific record, after checking the target and requested values.

Connect to the separate writer using your personal Redmine API key. Your administrator
must enable the writer and the action, and your account needs the native Redmine permissions
for the target. There is no separate account admission list.
See [Reader and writer access](access.md).

## Check your access

Confirm the account with `get_current_user`. To discover candidate actions for a project, ask:

```text
Show my candidate actions for the Website project, with reasons where available.
Explain which actions remain conditional or unknown. Do not change anything.
```

The client can resolve the project with `list_projects`, then use
`list_my_project_capabilities` with `project_id` and `include_reasons: true`.
The server checks permissions again when you perform an action. If the action is missing,
check [connection and writer setup](access.md).

## Make a change

1. Resolve the project or issue, review its current state, and specify the exact change.
   For an issue, agree on the project and subject; for a note, review the text;
   for time, choose the issue, hours, date, and activity.
2. Ask the client to perform the agreed action and return its receipt and record ID.
3. Review the outcome below, including differences or unavailable verification, before
   assuming every field changed.

If you want to review a draft first, say so explicitly:

```text
Draft a new issue for the Website project from this description.
Show me the proposed subject and description without creating it yet.
```

After reviewing, instruct the client to create the agreed issue. Drafting itself does not
require a write call. Client-specific approval controls may also apply.

**Choose a walkthrough**

- [Create an issue](create-issue.md)
- [Understand an issue and add a note](issue-summary.md)
- [Review and record time](time-report.md)

For versions, memberships, relations, watchers, attachments, note edits, or time-entry
corrections/deletion, see the [reference guide](reference.md). There is no general
issue-deletion tool or atomic multi-action transaction.

## Read the outcome

| Result | What it means | What to do |
| --- | --- | --- |
| Accepted, verification matched | Redmine accepted the action and the supported comparison matched | Review the returned record and field-level details |
| Accepted, verification mismatch | Redmine accepted the request but observed values differ | Inspect differences and native field/workflow rules |
| Accepted, verification unavailable | Acceptance is known, but the independent comparison could not finish | Inspect Redmine or read the record again if permitted |
| Uncertain | The action may have taken effect | Reconcile actual state before another attempt |
| Rejected/error | Inspect the reported cause | Correct access or inputs; do not infer failure when dispatch outcome is uncertain |

Receipt fields vary by operation. An outer transport success does not establish that a
mutation succeeded or all fields changed. Native rules can ignore uneditable fields or
reject required values.

Writes are attempted once by the server. Repeating a request can create duplicate issues,
notes, or time entries. After a timeout, lost response, or uncertain receipt, inspect
Redmine before deciding whether to retry. Matching text or hours alone does not prove
which call created a record.

