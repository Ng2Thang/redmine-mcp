# Redmine REST API — Issues

> Source: https://www.redmine.org/projects/redmine/wiki/Rest_Issues  
> Resource: Issues  
> Formats: JSON / XML  
> Extracted: 2026-09-29

## Endpoint Summary

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/issues.[format]` | List issues |
| `GET` | `/issues/[id].[format]` | Get a single issue |
| `POST` | `/issues.[format]` | Create an issue |
| `PUT` | `/issues/[id].[format]` | Update an issue |
| `DELETE` | `/issues/[id].[format]` | Delete an issue |
| `POST` | `/issues/[id]/watchers.[format]` | Add a watcher |
| `DELETE` | `/issues/[id]/watchers/[user_id].[format]` | Remove a watcher |

---

## 1. List Issues

### Request

```http
GET /issues.[format]
```

Returns a paginated collection of issues. By default, Redmine returns open issues.

### Parameters

| Name | Location | Required | Description |
|---|---|---:|---|
| `offset` | Query | No | Number of issues to skip. |
| `limit` | Query | No | Maximum number of issues returned per page. |
| `sort` | Query | No | Sort by one or more columns. Append `:desc` for descending order. |
| `include` | Query | No | Comma-separated associated resources to include. Supported values documented here include `attachments` and `relations`. |

### Filters

| Name | Required | Description |
|---|---:|---|
| `issue_id` | No | Filter by one issue ID or multiple comma-separated IDs. |
| `project_id` | No | Filter by numeric project ID. |
| `subproject_id` | No | Filter by subproject ID. `!*` can be used to exclude subprojects when combined with `project_id`. |
| `tracker_id` | No | Filter by tracker ID. |
| `status_id` | No | Filter by status. Supports a status ID as well as `open`, `closed`, or `*`. |
| `assigned_to_id` | No | Filter by assignee ID. `me` refers to the authenticated user. |
| `parent_id` | No | Filter issues by parent issue ID. |
| `cf_x` | No | Filter using custom field ID `x`; the custom field must be enabled as a filter. |
| Other issue filters | No | Redmine supports additional issue-query filters, including date/time operators. |

### Include Values

| Value | Notes |
|---|---|
| `attachments` | Available since Redmine 3.4.0 according to the source page. |
| `relations` | Includes issue relations. |

### Examples

```http
GET /issues.json
GET /issues.json?issue_id=1
GET /issues.json?issue_id=1,2
GET /issues.json?project_id=2
GET /issues.json?project_id=2&tracker_id=1
GET /issues.json?assigned_to_id=me
GET /issues.json?status_id=closed
GET /issues.json?status_id=*
GET /issues.json?cf_1=abcdef
GET /issues.json?sort=category:desc,updated_on
```

Pagination:

```http
GET /issues.json?offset=0&limit=100
GET /issues.json?offset=100&limit=100
```

Date/time filter examples:

```http
GET /issues.json?created_on=%3E%3D2012-03-01
GET /issues.json?created_on=%3C%3D2012-03-07
GET /issues.json?created_on=%3E%3D2014-01-02T08:12:32Z
GET /issues.json?updated_on=%3E%3D2014-01-02T08:12:32Z
GET /issues.json?cf_4=~foo
```

### Notes

Operators containing characters such as `>`, `<`, and `=` should be URL-encoded in query parameters.

### Response Shape

A successful list response contains a collection of issue objects. Common fields shown by Redmine include:

- `id`
- `project`
- `tracker`
- `status`
- `priority`
- `author`
- `category`
- `subject`
- `description`
- `start_date`
- `due_date`
- `done_ratio`
- `estimated_hours`
- `custom_fields`
- `created_on`
- `updated_on`

---

## 2. Show an Issue

### Request

```http
GET /issues/[id].[format]
```

Returns one issue by ID.

### Path Parameters

| Name | Required | Description |
|---|---:|---|
| `id` | Yes | Issue ID. |
| `format` | Yes | Response format, typically `json` or `xml`. |

### Query Parameters

| Name | Required | Description |
|---|---:|---|
| `include` | No | Comma-separated associated resources to include. |

### Include Values

| Value | Notes |
|---|---|
| `children` | Child issues. |
| `attachments` | Issue attachments. |
| `relations` | Issue relations. |
| `changesets` | Related changesets. |
| `journals` | Issue journals/history. |
| `watchers` | Watchers; documented as available since Redmine 2.3.0. |
| `allowed_statuses` | Available statuses based on workflow and issue constraints; documented since Redmine 5.0.x. |
| `reactions` | Users who reacted to the issue; documented since Redmine 7.1.0. |

### Examples

```http
GET /issues/2.json
GET /issues/2.json?include=attachments
GET /issues/2.json?include=attachments,journals
GET /issues/2.json?include=reactions
GET /issues/2.json?include=journals,reactions
```

### `allowed_statuses` Behavior

The available statuses can depend on:

- current tracker
- current issue status
- authenticated member role and configured workflow
- open subtasks
- open blocking issues
- whether the parent issue is closed

### `reactions` Behavior

When reactions are included, Redmine can return visible users who reacted to the issue. If journals are also included, journal reactions are included as well. The result is subject to visibility permissions and the reactions feature being enabled.

---

## 3. Create an Issue

### Request

```http
POST /issues.[format]
```

### Request Body

The top-level request object is `issue`.

### Issue Fields

| Field | Required | Description |
|---|---:|---|
| `project_id` | Depends on context | Project ID. |
| `tracker_id` | No | Tracker ID. |
| `status_id` | No | Status ID. |
| `priority_id` | No | Priority ID. |
| `subject` | Usually Yes | Issue subject/title. |
| `description` | No | Issue description. |
| `category_id` | No | Issue category ID. |
| `fixed_version_id` | No | Target version ID. |
| `assigned_to_id` | No | User ID to assign the issue to. |
| `parent_issue_id` | No | Parent issue ID. |
| `custom_fields` | No | Custom field values. |
| `watcher_user_ids` | No | Array of watcher user IDs; documented since Redmine 2.3.0. |
| `is_private` | No | Boolean indicating whether the issue is private. |
| `estimated_hours` | No | Estimated effort in hours. |

Attachments may also be added during issue creation using Redmine's upload/attachment API flow.

### JSON Example

```json
{
  "issue": {
    "project_id": 1,
    "subject": "Example",
    "priority_id": 4
  }
}
```

---

## 4. Update an Issue

### Request

```http
PUT /issues/[id].[format]
```

### Path Parameters

| Name | Required | Description |
|---|---:|---|
| `id` | Yes | Issue ID. |
| `format` | Yes | Request/response format, typically `json` or `xml`. |

### Request Body

The top-level request object is `issue`.

Redmine accepts issue attributes such as:

- `project_id`
- `tracker_id`
- `status_id`
- `subject`
- other editable issue attributes
- `notes`
- `private_notes`

### Special Fields

| Field | Required | Description |
|---|---:|---|
| `notes` | No | Comment/journal note associated with the update. |
| `private_notes` | No | Boolean; marks the note as private. |

Attachments can also be added while updating an issue.

### JSON Example

```json
{
  "issue": {
    "subject": "Subject changed",
    "notes": "The subject was changed"
  }
}
```

---

## 5. Delete an Issue

### Request

```http
DELETE /issues/[id].[format]
```

### Path Parameters

| Name | Required | Description |
|---|---:|---|
| `id` | Yes | Issue ID to delete. |
| `format` | Yes | API format, typically `json` or `xml`. |

---

## 6. Add a Watcher

Documented as available since Redmine 2.3.0.

### Request

```http
POST /issues/[id]/watchers.[format]
```

### Path Parameters

| Name | Required | Description |
|---|---:|---|
| `id` | Yes | Issue ID. |
| `format` | Yes | API format. |

### Body Parameter

| Name | Required | Description |
|---|---:|---|
| `user_id` | Yes | ID of the user to add as a watcher. |

### JSON Example

```json
{
  "user_id": 5
}
```

---

## 7. Remove a Watcher

Documented as available since Redmine 2.3.0.

### Request

```http
DELETE /issues/[id]/watchers/[user_id].[format]
```

### Path Parameters

| Name | Required | Description |
|---|---:|---|
| `id` | Yes | Issue ID. |
| `user_id` | Yes | User ID to remove from watchers. |
| `format` | Yes | API format. |

No request parameters are documented beyond the path values.

---

## Resource Model Summary

### Issue

Common issue attributes used across these endpoints include:

```text
id
project_id
tracker_id
status_id
priority_id
subject
description
category_id
fixed_version_id
assigned_to_id
parent_issue_id
custom_fields
watcher_user_ids
is_private
estimated_hours
start_date
due_date
done_ratio
created_on
updated_on
```

## Related Redmine REST Resources

The source page links to related documentation for:

- Issue journals
- Custom fields
- File uploads / attachments

## Source

Redmine REST Issues documentation:

https://www.redmine.org/projects/redmine/wiki/Rest_Issues
