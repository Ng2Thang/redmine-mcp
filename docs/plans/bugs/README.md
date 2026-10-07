# Bug task plans

Store bug investigation and fix plans in this folder. Use one document per bug,
named `bug-NNN-short-description.md`, starting with `bug-001`.

Copy [TEMPLATE.md](TEMPLATE.md) for each new plan. Record the affected behavior,
reproduction steps, expected result, proposed fix, and acceptance criteria.
Link each assigned bug task and its current status from [the planning index](../index.md).

Use the existing task statuses: `discovery`, `specified`, `planned`, `implementing`,
`verifying`, `complete`, or `blocked`. A completed plan or implementation does not
establish verification. Record missing evidence and the next action explicitly.

Creating a plan does not authorize implementation or testing. Run tests, startup,
Inspector, or other verification tools only when the user explicitly authorizes them.
Keep credentials and private data out of reproduction steps and evidence.
