"""Export and serve documentation without importing or configuring the MCP application."""

from __future__ import annotations

import argparse
import functools
import io
import json
import os
import re
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import IO
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

    shell_files = (
        "index.html", "home.md", "404.md", "_sidebar.md", "_navbar.md", "_coverpage.md",
    )
    for name in shell_files:
        copy_file(SOURCE / name, staging / name)
    for source in sorted((SOURCE / "guides").glob("*.md")):
        if not source.name.startswith("."):
            copy_file(source, staging / source.relative_to(SOURCE))
    # Only the dedicated translated Markdown tree is exported for the Vietnamese edition.
    for source in sorted((SOURCE / "vi").rglob("*.md")):
        if not any(part.startswith(".") for part in source.relative_to(SOURCE / "vi").parts):
            copy_file(source, staging / source.relative_to(SOURCE))
    # An explicit asset inventory prevents stray private files in assets from being published.
    asset_paths = {
        "assets/portal.css", "assets/portal.js", "assets/theme.js", "assets/language.js",
        "assets/favicon.svg",
        "assets/examples/issue-request.svg", "assets/examples/issue-result.svg",
        "assets/examples/issue-flow.png", "assets/examples/issue-flow.gif",
        "assets/examples/my-issues.svg", "assets/examples/project-discovery.svg",
        "assets/imgs/install_mcp_codex_vscode_ext.png",
        "assets/imgs/implement-stock-feature-example.png",
        "assets/imgs/example_redmine_tool.png",
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

    server: PortalServer

    def list_directory(self, path: str) -> None:
        self.send_error(404, "Directory listing is disabled")

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        with self.server.reload_lock:
            super().do_GET()

    def do_HEAD(self) -> None:
        with self.server.reload_lock:
            super().do_HEAD()

    def send_head(self) -> IO[bytes] | None:
        path = urlsplit(self.path).path
        if path == "/__portal_revision":
            content = self.server.revision.encode("utf-8")
            content_type = "text/plain; charset=utf-8"
        elif path in {"/", "/index.html"}:
            content = safe_path(OUTPUT_PARENT / "site" / "index.html").read_bytes()
            # Inject only in the development server; static exports remain standalone.
            script = """<script>
(function () {
  const revision = REVISION;
  async function poll() {
    try {
      const response = await fetch('/__portal_revision', { cache: 'no-store' });
      if (response.ok && (await response.text()) !== revision) {
        window.location.reload();
        return;
      }
    } catch (_) { /* Retry while the development server is unavailable. */ }
    window.setTimeout(poll, 1000);
  }
  window.setTimeout(poll, 1000);
}());
</script>""".replace("REVISION", json.dumps(self.server.revision))
            content = content.replace(b"</body>", script.encode("utf-8") + b"\n</body>")
            content_type = "text/html; charset=utf-8"
        else:
            return super().send_head()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        return io.BytesIO(content)

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        if urlsplit(self.path).path != "/__portal_revision":
            super().log_request(code, size)


def source_snapshot() -> dict[str, tuple[int, int]]:
    """Watch export inputs, including new guides, using portable filesystem polling."""
    manifest = json.loads(
        safe_path(OUTPUT_PARENT / "site" / "export-manifest.json").read_text(encoding="utf-8")
    )
    paths = {ROOT / name for name in manifest["documents"] + manifest["references"]}
    paths.update(ROOT / name for name in tracked_files() if name.startswith("docs/"))
    paths.update(
        SOURCE / name for name in
        ("index.html", "home.md", "404.md", "_sidebar.md", "_navbar.md", "_coverpage.md")
    )
    for directory, pattern in (("guides", "*.md"), ("vi", "*.md"), ("assets", "*")):
        paths.update((SOURCE / directory).rglob(pattern))
    snapshot = {}
    for path in sorted(paths):
        safe_path(path)
        try:
            if path.is_file():
                stat = path.stat()
                snapshot[path.relative_to(ROOT).as_posix()] = (stat.st_mtime_ns, stat.st_size)
        except FileNotFoundError:
            # Editors can briefly replace a file while saving it.
            continue
    return snapshot


class PortalServer(ThreadingHTTPServer):
    """Re-export changed inputs while serializing exports with file requests."""

    def __init__(
        self, address: tuple[str, int], handler: functools.partial[PortalHandler],
    ) -> None:
        self.reload_lock = threading.RLock()
        self.revision = str(time.time_ns())
        self.snapshot = source_snapshot()
        self.next_scan = time.monotonic() + 1
        super().__init__(address, handler)

    def service_actions(self) -> None:
        if time.monotonic() < self.next_scan:
            return
        self.next_scan = time.monotonic() + 1
        try:
            snapshot = source_snapshot()
            if snapshot == self.snapshot:
                return
            with self.reload_lock:
                export()
                self.snapshot = snapshot
                self.revision = str(time.time_ns())
            print("Documentation changed; browser reload requested.", flush=True)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            print(f"Documentation reload failed; retrying: {error}", flush=True)


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
        with PortalServer(("127.0.0.1", arguments.port), handler) as server:
            print(f"Documentation: http://127.0.0.1:{arguments.port}/ (Ctrl+C to stop)")
            print("Watching documentation and assets for changes (automatic browser reload).")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nDocumentation server stopped.")


if __name__ == "__main__":
    main()
