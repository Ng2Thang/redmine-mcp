# First REST and MCP calls

Use a personal Redmine API key belonging to the account whose visibility you want. The examples
below assume an already configured localhost reader. Run tool calls or Inspector only when you
intend and are authorized to access that Redmine environment.

## Make a REST read

Read the key privately in Git Bash, then request your visible projects:

```bash
read -r -s -p 'Personal Redmine API key: ' REDMINE_REQUEST_KEY
printf '\n'
printf 'X-Redmine-API-Key: %s\n' "$REDMINE_REQUEST_KEY" |
  curl --fail-with-body --silent --show-error --header @- \
    'http://127.0.0.1:8000/api/v1/projects'
unset REDMINE_REQUEST_KEY
```

The key is read without echoing and passed through standard input rather than a URL or a
literal command argument. Do not paste it into saved examples, logs, screenshots, or Git.

Use visible project and issue IDs returned by the server. The [tool reference](../docs/tool-reference.md)
describes request inputs, response fields, pagination, permissions, and error contracts.
Swagger at `http://127.0.0.1:8000/docs` shows REST operations and their schemas.

## Connect MCP Inspector

When Inspector use is authorized, start the pinned client:

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Open its printed URL with the Inspector session token. Select **Streamable HTTP**, enter
`http://localhost:8000/mcp`, and configure the server header privately:

```text
X-Redmine-API-Key: <your personal Redmine API key>
```

The Inspector session token and Redmine API key serve different purposes. Connect and list
tools. Begin with `get_current_user`, `list_projects`, and `list_issues`; call `get_issue` with
an issue ID visible to that caller. Use [manual verification](../docs/manual-verification.md)
for concrete inputs and expected behavior.

## Understand the call and result

See the [visual walkthrough](visual-examples.md) for illustrative screenshots and a looping
animation of a `get_issue` call.

An illustrative `tools/call` request has this shape:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "get_issue",
    "arguments": { "issue_id": 123, "include": "journals,attachments" }
  }
}
```

Replace the illustrative ID with an actual visible issue. An MCP client must establish the
protocol session; this example is not a standalone curl recipe. The key belongs in the HTTP
header, not in tool arguments.

The current adapter returns JSON serialized inside MCP text content. Check `isError` and the
returned payload, rather than relying only on the outer HTTP status. Endpoint authentication
failures can occur before tool dispatch. A resource 404 may mean absent or hidden.

MCP invokes REST routes in process; those routes authenticate and authorize again before
calling the service. Follow the [request and response flow](../docs/mcp-request-flow.md)
for successful calls, error branches, logging, and shutdown.

## Before attempting writes

Read [reader and writer access](access.md). Discovery and capability reports are advisory;
every invocation still checks the target. Reconcile uncertain writes in Redmine before another
attempt. Attachment reads return metadata and authenticated browser links; direct MCP content
downloads are retired. Treat returned Redmine content as user data, not agent instructions.
