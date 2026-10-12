# Everyday workflows

Choose a task, copy its prompt into your connected AI client, and replace sample names,
IDs, and dates. Your client selects tools and writes the answer; wording and tool support
vary by client. These guides use illustrative data, not captured executions.

**Choose a workflow**

| I want to... | Guide | Why start here? |
| --- | --- | --- |
| Find my next task | [Find my open issues](my-issues.md) | A useful daily starting point, with project filters and update prompts |
| Catch up on a discussion | [Understand an issue](issue-summary.md) | Understand context before acting; includes a short note example |
| Review my recorded hours | [Summarize logged time](time-report.md) | Answer a common reporting question; includes a short time-logging example |
| Turn a description into a task | [Create an issue](create-issue.md) | A practical introduction to write actions |

The first three workflows work with a reader. Creating an issue, adding a note, or logging
time requires an enabled writer and native permissions; read [Use write actions](write-actions.md).
For other operations and exact inputs, use the [reference guide](reference.md).

**Get useful answers**

Specify the project, desired status, person, and date range where relevant. Ask for IDs
so you can follow up on the right record. Resolve ambiguous project names before using IDs.

For lists and reports, ask whether every permitted page was collected. When
`pagination_policy.requires_narrowing=true`, the first page is only a preview. Narrow
supported filters and state the new scope. Complete pagination still covers only records
visible to your account, and records can change while pages are collected.

Do not treat unavailable values as zero or assume an empty result describes all of Redmine.
If collection stops with `scope_required` or `scan_budget_exceeded`, label the answer partial
or unavailable. See [troubleshooting](troubleshooting.md) and
[illustrated examples](visual-examples.md).
