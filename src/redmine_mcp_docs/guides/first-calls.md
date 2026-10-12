# REST and Inspector examples

For the shortest path to a useful answer, follow [MCP client installation](get-started.md).
This optional reference provides direct REST requests and MCP Inspector examples after
the server is running. For normal AI-client setup, use the client installation guide above.

**Connection values**

| Setting | Local reader example |
| --- | --- |
| MCP transport | Streamable HTTP |
| MCP URL | `http://127.0.0.1:8000/mcp` |
| Authentication header | `X-Redmine-API-Key: <your personal Redmine API key>` |
| REST base URL | `http://127.0.0.1:8000/api/v1` |
| REST schemas | `http://127.0.0.1:8000/docs` |

Use your administrator's URL for a remote server. Each request uses your personal Redmine
identity. Put the key in private HTTP header settings, never tool arguments.

## Optional: connect with MCP Inspector

Inspector is a tool explorer you can use without another compatible client. It requires
Node.js/npm. Start it from Git Bash:

```bash
npx @modelcontextprotocol/inspector@2.8.0
```

Open the printed URL with its Inspector session token. Select **Streamable HTTP**, enter
the MCP URL, and privately configure `X-Redmine-API-Key` with your personal key. The
Inspector session token and Redmine API key are different credentials.

Connect, list tools, and call `get_current_user` with `{}`. Confirm your account, then call
`list_projects` with `{"limit": 25, "offset": 0}`. Use returned IDs for further requests.
Use the workflow guides to turn tool results into issue summaries and reports.

## Optional: make a REST read

This Git Bash example prompts for your key without echoing it and requests visible projects:

```bash
read -r -s -p 'Personal Redmine API key: ' REDMINE_REQUEST_KEY
printf '\n'
printf 'X-Redmine-API-Key: %s\n' "$REDMINE_REQUEST_KEY" |
  curl --fail-with-body --silent --show-error --header @- \
    'http://127.0.0.1:8000/api/v1/projects'
unset REDMINE_REQUEST_KEY
```

The key is passed through standard input. Keep it out of saved examples, screenshots,
logs, and Git. `total` describes matching caller-visible records, while `items` contains
only the records in this page.

## Understand results

A client can call `get_issue` with illustrative input:

```json
{"issue_id": 123, "include": "journals,attachments"}
```

Replace `123` with a visible issue ID. MCP clients establish a protocol session before
calling tools; tool arguments alone are not a standalone HTTP request.

The adapter returns JSON inside MCP text content. Check `isError` and the payload in
Inspector, since an outer HTTP success can contain a tool error. Ask your AI client to
surface errors, missing fields, and incomplete pagination in its answer.

Use [troubleshooting](troubleshooting.md) for help and the [reference guide](reference.md)
for precise inputs and results. Before changes, read [Use write actions](write-actions.md).
