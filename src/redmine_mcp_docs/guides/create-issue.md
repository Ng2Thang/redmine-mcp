# Create an issue

Turn a work description into one issue in the intended Redmine project.

You need an enabled writer with `create_issue`, permission to add issues in the target project,
and any values required by its workflow. Read [Use write actions](write-actions.md).

## Create the issue

```text
Create one issue in the Website project with subject "Fix login redirect".
Description: "After signing in, return users to the page they originally requested."
Use the project's defaults for fields I have not specified.
Show the new issue ID and whether the supplied values were verified.
```

**How it works**

1. Resolve the project with `list_projects`; confirm the destination.
2. Review the subject and description. If you only want a draft, say "do not create it yet".
3. Call `create_issue` with the resolved ID. Synthetic input:

```json
{"project_id": 10, "subject": "Fix login redirect", "description": "After signing in, return users to the page they originally requested."}
```

4. Read `outcome`, `resource_id`, and field verification. Inspect the new issue when a
   comparison is unavailable or differs from the request.

**Example result**

> Created issue #135 in Website. Redmine accepted the request; the supported comparison
> matched the supplied values.
> Illustrative answer only, not a captured execution or guaranteed outcome.

## Choose issue fields

Specify a known tracker, priority, assignee, category, or Target version ID when required.
Resolve categories and versions through their listing tools rather than inventing IDs.
Dates use `YYYY-MM-DD`; assignee can be a positive numeric ID or `"me"`.
Native copying is documented separately in the [tool reference](../docs/tool-reference.md).

## Failed or uncertain creation

Required custom fields, tracker rules, or workflow permissions may prevent creation.
Identify missing inputs rather than repeatedly submitting the same request. After an
uncertain outcome, inspect the project in Redmine before another attempt; retrying can
create a duplicate even if no ID was returned.

**Related tools and next steps**

`list_projects`, `list_project_issue_categories`, `list_project_versions`, `create_issue`.
Continue with [Understand an issue](issue-summary.md), including its note example.
