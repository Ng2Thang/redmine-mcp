# Reader and writer access

Every caller uses a personal Redmine API key. Redmine remains responsible for native project,
issue, attachment, membership, and time-entry permissions.

## Deployment comparison

| Behavior | Default reader | Separate opt-in writer |
| --- | --- | --- |
| Default local port | `8000` | `8001` |
| Read operations | 18 registered reads | Read catalog plus configured writes |
| Mutation admission | Disabled | Requires explicit enablement and operation gates |
| Caller identity | Personal Redmine key | Pinned-key or personal-key admission |
| Target permissions | Native Redmine visibility | Native permissions plus writer checks |

The complete registered write catalog has 18 operations. A particular writer may expose fewer,
depending on configured operations and caller-specific discovery.

## Configure a writer

Follow [separate writer deployment](../docs/configuration.md#separate-writer-deployment) and
[writer operations](../docs/operations.md#separate-writer). Use a separate private environment
file and listener. Enabling the reader is not part of the writer workflow.

Writer admission requires `REDMINE_WRITE_ENABLED=true` and a configured operation list.
`pinned_key` mode additionally requires a private key digest and admitted user IDs.
`personal_key` mode authenticates each caller independently and can restrict admission by user ID.
An empty operation setting admits no mutations.

An explicit operation list fixes the allowed ceiling. Standalone `allowed_all` permits every
registered write, including new registrations after an upgrade. Choose intentionally and
recreate or restart the writer as documented when changing configuration.

## Discovery is not permission

Personal-key discovery considers visible projects and bounded request-local membership/role
evidence. A listed operation can remain conditional or unknown for a specific target. The
capability report is advisory; invocation rechecks deployment gates, caller admission, target
visibility, and native permissions.

## Handle mutation outcomes

Writes are dispatched once. The receipt distinguishes acceptance, uncertainty, and subsequent
read-back observations. A successful transport response does not automatically establish that
every requested field changed. A missing read-back resource does not prove an uncertain delete
committed. Inspect native state before deciding whether another attempt is appropriate.

Read [mutation uncertainty](../docs/tool-reference.md#mutation-uncertainty) and each operation's
contract before performing changes. Synthetic administration, fixture cleanup, and database
access remain separate from MCP tools.
