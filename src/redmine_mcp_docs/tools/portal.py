"""Export and serve documentation without importing or configuring the MCP application."""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import shutil
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "src" / "redmine_mcp_docs"
OUTPUT_PARENT = ROOT / ".local" / "docs-portal"
MARKER = ".docs-portal-output"
OWNER = "redmine-mcp-docs-portal-v1\n"
ROOT_DOCUMENTS = (
    "README.md", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md",
)
ROOT_REFERENCES = {"pyproject.toml", "uv.lock", ".python-version", ".env.example", "LICENSE"}
REFERENCE_ROOTS = ("src/redmine_mcp/", "scripts/", "deploy/", "tests/", "tools/seed/")
REFERENCE_SUFFIXES = {".py", ".sh", ".toml", ".yaml", ".yml", ".json", ".rb"}
DOCUMENT_SUFFIXES = {".md", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}
NEW_DOCUMENTS = {"docs/documentation-portal.md"}
NEW_REFERENCES = {"scripts/docs-portal.sh"}
LINK = re.compile(
    r"\]\(<?([^\s)>]+)>?(?:\s+[^)]*)?\)|^\s*\[[^]]+\]:\s*<?([^\s>]+)>?", re.M,
)


def safe_path(path: Path) -> Path:
    """Reject redirected paths before reading, copying, removing, or serving them."""
    if not path.is_relative_to(ROOT):
        raise ValueError("Portal paths must remain inside the repository")
    current = path
    while current != ROOT:
        if current.is_symlink() or current.is_junction():
            raise ValueError(f"Redirected path is not allowed: {path.relative_to(ROOT)}")
        current = current.parent
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError("Resolved portal path escapes the repository")
    return resolved


def remove_output(path: Path) -> None:
    safe_path(path)
    if path.parent != OUTPUT_PARENT or path.name not in {"site", "staging"}:
        raise ValueError("Refusing to remove a directory outside the fixed portal output")
    if not path.exists():
        return
    marker = safe_path(path / MARKER)
    if not path.is_dir() or not marker.is_file() or marker.read_text() != OWNER:
        raise ValueError(f"Refusing to replace unmarked output: {path.relative_to(ROOT)}")
    shutil.rmtree(path)


def copy_file(source: Path, destination: Path) -> None:
    safe_path(source)
    safe_path(destination)
    if not source.is_file():
        raise ValueError(f"Required file is missing: {source.relative_to(ROOT)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def tracked_files() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True,
    )
    return set(result.stdout.decode("utf-8").rstrip("\0").split("\0"))


def reference_allowed(relative: str, tracked: set[str]) -> bool:
    if relative not in tracked and relative not in NEW_REFERENCES:
        return False
    if relative in ROOT_REFERENCES:
        return True
    return relative.startswith(REFERENCE_ROOTS) and Path(relative).suffix in REFERENCE_SUFFIXES


def export() -> Path:
    tracked = tracked_files()
    safe_path(OUTPUT_PARENT)
    OUTPUT_PARENT.mkdir(parents=True, exist_ok=True)
    site = OUTPUT_PARENT / "site"
    staging = OUTPUT_PARENT / "staging"
    # Check ownership of existing output before making any replacements.
    for path in (site, staging):
        safe_path(path)
        if path.exists():
            marker = safe_path(path / MARKER)
            if not marker.is_file() or marker.read_text() != OWNER:
                raise ValueError(f"Output directory has no portal ownership marker: {path}")
    remove_output(staging)
    staging.mkdir()
    (staging / MARKER).write_text(OWNER, encoding="utf-8")
    (staging / ".nojekyll").touch()

    shell_files = ("index.html", "home.md", "404.md", "_sidebar.md", "_navbar.md")
    for name in shell_files:
        copy_file(SOURCE / name, staging / name)
    for source in sorted((SOURCE / "guides").glob("*.md")):
        if not source.name.startswith("."):
            copy_file(source, staging / source.relative_to(SOURCE))
    # An explicit asset inventory prevents stray private files in assets from being published.
    asset_paths = {
        "assets/portal.css", "assets/portal.js", "assets/theme.js", "assets/favicon.svg",
        "assets/vendor/manifest.json", "assets/vendor/THIRD_PARTY_NOTICES.md",
    }
    vendor_manifest = safe_path(SOURCE / "assets" / "vendor" / "manifest.json")
    for package in json.loads(vendor_manifest.read_text(encoding="utf-8"))["packages"]:
        for entry in package["files"]:
            relative = Path(entry["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Vendor assets must stay within the vendor directory")
            asset_paths.add((Path("assets/vendor") / relative).as_posix())
    for relative in sorted(asset_paths):
        copy_file(SOURCE / relative, staging / relative)

    documents = set(ROOT_DOCUMENTS) | NEW_DOCUMENTS
    documents.update(
        name for name in tracked
        if name.startswith("docs/") and Path(name).suffix.lower() in DOCUMENT_SUFFIXES
        and (ROOT / name).exists()
    )
    for relative in sorted(documents):
        copy_file(ROOT / relative, staging / relative)
    # Docsify reserves root README for its homepage, so publish a distinct quick-start route.
    copy_file(ROOT / "README.md", staging / "repository.md")

    # Preserve linked source/configuration references, never copy the repository wholesale.
    references: set[str] = set()
    for document in sorted(staging.rglob("*.md")):
        original = ROOT / document.relative_to(staging)
        for match in LINK.finditer(document.read_text(encoding="utf-8")):
            url = urlsplit(match.group(1) or match.group(2))
            if url.scheme or url.netloc or not url.path or url.path.startswith("/"):
                continue
            target = Path(os.path.abspath(original.parent / unquote(url.path)))
            if not target.is_relative_to(ROOT):
                continue
            relative = target.relative_to(ROOT).as_posix()
            if reference_allowed(relative, tracked) and target.exists():
                copy_file(ROOT / relative, staging / relative)
                references.add(relative)

    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    (staging / "export-manifest.json").write_text(
        json.dumps({
            "revision": revision,
            "content": "Current working-tree contents; revision is a reference, not acceptance.",
            "documents": sorted(documents), "references": sorted(references),
            "files": sorted(
                path.relative_to(staging).as_posix()
                for path in staging.rglob("*") if path.is_file()
            ),
        }, indent=2) + "\n", encoding="utf-8",
    )
    remove_output(site)
    safe_path(staging)
    safe_path(site)
    staging.rename(site)
    print(f"Exported documentation to {site.relative_to(ROOT).as_posix()}/")
    return site


class PortalHandler(SimpleHTTPRequestHandler):
    """Serve exported files without directory listings."""

    def list_directory(self, path: str) -> None:
        self.send_error(404, "Directory listing is disabled")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("export", "serve"))
    parser.add_argument("port", nargs="?", type=int, default=8080)
    arguments = parser.parse_args()
    if not 1 <= arguments.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    site = export()
    if arguments.command == "serve":
        handler = functools.partial(PortalHandler, directory=str(site))
        with ThreadingHTTPServer(("127.0.0.1", arguments.port), handler) as server:
            print(f"Documentation: http://127.0.0.1:{arguments.port}/ (Ctrl+C to stop)")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nDocumentation server stopped.")


if __name__ == "__main__":
    main()
