"""Compare Python syntax trees before and after formatting without importing source."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fingerprints(targets: list[str]) -> dict[str, str]:
    files: set[Path] = set()
    for target in targets:
        directory = (ROOT / target).resolve()
        if not directory.is_relative_to(ROOT) or not directory.is_dir():
            raise ValueError(f"Expected a repository directory: {target}")
        files.update(directory.rglob("*.py"))
    if not files:
        raise ValueError("No Python source files found")
    result: dict[str, str] = {}
    for path in sorted(files):
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"Source file resolves outside the repository: {path}")
        tree = ast.parse(path.read_bytes(), filename=str(path), type_comments=True)
        # TypeIgnore stores line numbers as fields; ignore positions but retain its tag.
        for node in ast.walk(tree):
            if isinstance(node, ast.TypeIgnore):
                node.lineno = 0
        structure = ast.dump(tree, include_attributes=False)
        result[path.relative_to(ROOT).as_posix()] = hashlib.sha256(structure.encode()).hexdigest()
    return result


def read_snapshot(path: Path) -> dict[str, str]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Invalid syntax-tree snapshot")
    result: dict[str, str] = {}
    for key, digest in value.items():
        if not isinstance(key, str) or not isinstance(digest, str):
            raise ValueError("Invalid syntax-tree snapshot entry")
        result[key] = digest
    if not result:
        raise ValueError("Empty syntax-tree snapshot")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("snapshot", "compare"))
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("targets", nargs="+")
    arguments = parser.parse_args()
    current = fingerprints(arguments.targets)
    if arguments.mode == "snapshot":
        arguments.snapshot.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"Captured syntax trees for {len(current)} Python files.")
        return 0
    before = read_snapshot(arguments.snapshot)
    names = before.keys() | current.keys()
    changed = sorted(name for name in names if before.get(name) != current.get(name))
    if changed:
        print("Formatting syntax-tree comparison failed; inspect the retained source diff:")
        for name in changed:
            print(f"  {name}")
        return 1
    print(f"Formatting preserved syntax trees for {len(current)} Python files.")
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except (OSError, ValueError, SyntaxError, RecursionError) as exc:
        print(f"Syntax-tree guard failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    raise SystemExit(exit_code)
