# bug-001: get_issue fails with upstream_response

## Tracking

- Status: blocked
- Reported date: 2026-10-07
- Report reference: `2026-10-07 15:15:02,159 ERROR fastapi_mcp.server`;
  request ID `1351004e3025414c8921e1d7e6eba69c`.
- Affected tool: `get_issue`
- Affected components: issue reader, Redmine response parsing, REST-to-MCP error conversion.
- Dependencies or blockers: exact arguments and sanitized upstream evidence are missing.
- Next action: obtain the failing issue's sanitized Redmine JSON response and exact call
  arguments; identify the rejecting boundary before changing runtime validation.

## Problem and impact

The user reports that calling `get_issue` fails with `upstream_response` and the message
`Unexpected Redmine data`. The caller cannot retrieve the requested issue through MCP.
The frequency, affected issue range, and whether REST requests also fail are unknown.

## Reproduction

- Reported environment: Windows workspace at `D:\redmine-mcp`, using the local `.venv`.
- Redmine, application revision, Python, fastapi-mcp, and HTTPX versions: not supplied.
- Preconditions: an MCP deployment exposing `get_issue`; caller access to the target
  issue must be established during investigation.
- Reported action: call `get_issue`. Exact issue ID and include arguments were not supplied.
- Actual result: the call fails with the error and traceback below.
- Expected result: a valid, visible Redmine issue returns the documented issue detail.
  If the upstream response is invalid, preserve the safe documented error behavior.
- Reproduction status: user-reported; not independently reproduced.

### Reported traceback

```text
2026-10-07 15:15:02,159 ERROR fastapi_mcp.server request_id=1351004e3025414c8921e1d7e6eba69c Error calling get_issue
Traceback (most recent call last):
  File "D:\redmine-mcp\.venv\Lib\site-packages\fastapi_mcp\server.py", line 544, in _execute_api_tool
    response = await self._request(client, method, path, query, headers, body)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\redmine-mcp\src\redmine_mcp\mcp\compatibility.py", line 153, in request
    return await original(client, method, path, query, headers, body)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\redmine-mcp\.venv\Lib\site-packages\fastapi_mcp\server.py", line 582, in _request
    return await client.get(path, params=query, headers=headers)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\redmine-mcp\.venv\Lib\site-packages\httpx\_client.py", line 1768, in get
    return await self.request(
           ^^^^^^^^^^^^^^^^^^^
    ...<9 lines>...
    )
    ^
  File "D:\redmine-mcp\src\redmine_mcp\mcp\read_limits.py", line 37, in request
    raise RuntimeError(json.dumps({"error": error}, ensure_ascii=False))
RuntimeError: {"error": {"code": "upstream_response", "message": "Unexpected Redmine data"}}
```

## Investigation

Confirmed by source inspection:

- [MCPRestClient.request](../../../src/redmine_mcp/mcp/read_limits.py) raises a
  `RuntimeError` when the internal REST response is an error. It retains sanitized
  application error fields. Line 37 is the conversion point, not proof of the root cause.
- [The issue gateway](../../../src/redmine_mcp/integrations/redmine/issues.py) fetches
  `issues/{issue_id}.json`, validates the issue resource, and converts it to `IssueDetail`.
  When include arguments are omitted, it requests journals and attachments.
- [The Redmine client](../../../src/redmine_mcp/integrations/redmine/client.py) parses
  upstream JSON and maps attachment links before returning data to the issue gateway.

Hypotheses requiring evidence: a valid response shape may be rejected by issue or nested
field validation; attachment metadata may fail link validation; or Redmine may have returned
unexpected data. The traceback does not establish any of these causes or a regression.

Investigation needs:

1. Record the exact call arguments and relevant versions without credentials.
2. Obtain sanitized field names, types, and validation locations for the failing response.
   Do not place issue descriptions, private journals, tokens, or raw production payloads here.
3. Determine whether rejection happens during upstream parsing, attachment mapping,
   resource identity validation, or issue model conversion.
4. Determine whether includes affect the failure and whether REST and MCP agree.
   Executing requests or verification requires separate user authorization.

## Proposed fix

No implementation is selected until the cause is confirmed. If supported valid Redmine
data is rejected, correct the responsible parsing or model contract narrowly. If the
response is invalid, preserve rejection and identify the upstream correction required.
Preserve strict validation, permission boundaries, error sanitization, and the stable
`get_issue` operation ID. Do not suppress errors or broadly loosen field validation.

## Acceptance criteria

- The reported input and rejecting boundary are identified with sanitized evidence.
- A valid affected issue returns the documented result through REST and MCP after a fix.
- Relevant journal and attachment include behavior remains compatible.
- Invalid upstream data still produces a sanitized application error without private data.
- Completion records implementation and separately authorized verification evidence.

## Verification plan and authorization

- Proposed scenarios: the reported response shape, a normal issue, relevant include
  combinations, and malformed data at the confirmed failing boundary.
- Required dependencies or fixtures: a sanitized minimal response or synthetic equivalent,
  exact caller arguments, relevant versions, and an authorized environment for live checks.
- User authorization: ticket creation, source inspection, and bug implementation; testing
  and live verification remain unauthorized.
- Execution results: no tests, startup, Inspector, or live requests run.
- Limitations: root cause and reproducibility remain unconfirmed.

## Implementation and handoff

- Changes made: ticket created; planning index updated.
- Runtime changes: none.
- Verification evidence: supplied traceback and read-only source inspection only.
- Remaining work: collect missing evidence, confirm cause, implement the fix under the current
  assignment, and obtain separate verification authorization.

### Implementation investigation: 2026-10-07

The user authorized fixing this ticket. No runtime patch was selected because the failing
response is unavailable and the reported error is shared by multiple validation boundaries.
The user's follow-up repeated the sanitized error without supplying call arguments or data.

- Inspected response envelope/identity checks, issue models, model conversion, and attachment
  link validation. Each remains a possible rejection boundary; none is confirmed as the cause.
- Read the locally available Redmine 7.0.2 `app/views/issues/show.api.rsb` source. This establishes
  the target response structure, but the failing deployment version remains unknown.
- Inspected field types in the existing `.local/get_issue.json` without displaying issue values.
  It contains a saved successful tool result, not the failing upstream response, so it cannot
  establish the cause or serve as acceptance evidence for this report.
- Ran `bash scripts/doctor.sh` through Git Bash: required prerequisites passed.
- No runtime code or tests changed. Ruff/mypy were not run because no Python code changed.
- Implementation is blocked on the failing input/response evidence. Verification remains
  separately pending. Do not treat the generic error conversion as the underlying defect.

### Follow-up report: full log prefix

The user supplied the complete log prefix with timestamp and request ID above. The stack
and sanitized error are unchanged. Source inspection confirms that the REST error handler
logs the application error code and status, while model conversion discards the underlying
validation exception. An earlier correlated log may provide context, but this traceback
alone does not identify the rejected field or response boundary.

- Requested exact `get_issue` arguments and sanitized upstream response evidence.
- No runtime changes, tests, static checks, startup, or live requests performed.
- Status remains blocked pending the failing input/response evidence.
