"""Check operation/owner coverage and preserve private source digests for prep-020."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from redmine_mcp.auth import READ_OPERATIONS, WRITE_OPERATIONS  # noqa: E402
from redmine_mcp.mcp.catalog import OPERATIONS, writer_catalog  # noqa: E402


def main() -> None:
    ledger = ROOT / "docs/plans/current-catalog-acceptance.md"
    rows = [
        line for line in ledger.read_text(encoding="utf-8").splitlines() if line.startswith("| `")
    ]
    names = [re.match(r"\| `([^`]+)`", row).group(1) for row in rows]
    expected = set(READ_OPERATIONS) | set(WRITE_OPERATIONS)
    assert len(names) == len(set(names)) == 32 and set(names) == expected
    assert tuple(READ_OPERATIONS) == OPERATIONS
    assert set(writer_catalog(frozenset(WRITE_OPERATIONS))) == expected
    for row in rows:
        fields = row.split("|")
        assert all(field.strip() for field in fields[1:-1])
        owners = re.findall(r"\]\((tasks/[^)]+)\)", fields[2])
        assert owners and all((ledger.parent / path).is_file() for path in owners)
        assert "R020 / 2026-10-07" in fields[3]
    sources = []
    for directory in ("src", "tests", "scripts", "tools/testing"):
        sources.extend(
            path for path in (ROOT / directory).rglob("*") if path.suffix in {".py", ".rb", ".sh"}
        )
    hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(sources)
    }
    state = ROOT / ".local/testing-e2e/prep-020" / ("audit-" + uuid4().hex)
    state.mkdir(parents=True)
    (state / "evidence.json").write_text(
        json.dumps(
            {
                "owner": "prep-020",
                "date": "2026-10-07",
                "operations": names,
                "revision": subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "working_tree": "uncommitted changes included in source digests",
                "sha256": hashes,
            },
            indent=2,
        )
    )
    print(
        "Prep-020 ledger audit passed: 17 reads, 15 writes, unique rows, owners and source digests."
    )


if __name__ == "__main__":
    main()
