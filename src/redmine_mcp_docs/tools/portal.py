"""Export and serve documentation without importing or configuring the MCP application."""

from __future__ import annotations

import argparse
import functools
import io
import json
import posixpath
import re
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import IO
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "src" / "redmine_mcp_docs"
OUTPUT_PARENT = ROOT / ".local" / "docs-portal"
MARKER = ".docs-portal-output"
OWNER = "redmine-mcp-docs-portal-v1\n"
SIDEBAR_LINK = re.compile(r"\]\((/[^)]*)\)")
OVERVIEW_GUIDES = ("module-map", "testing", "verification", "visual-examples")
OVERVIEW_REFERENCES = (
    "configuration", "tool-reference", "manual-verification", "architecture",
    "mcp-request-flow", "development", "workflows/redmine-tools", "operations",
    "test-data", "plans/testing-coverage", "plans/index", "documentation-portal",
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^\s)]+)\)")
REPOSITORY_FILES = "https://github.com/Ng2Thang/redmine-mcp/blob/master/"


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


def sidebar_pages() -> dict[str, str]:
    """Use the visible sidebar as the publication and search inventory."""
    pages: dict[str, str] = {}
    sidebar = safe_path(SOURCE / "_sidebar.md")
    for route in SIDEBAR_LINK.findall(sidebar.read_text(encoding="utf-8")):
        relative = route.lstrip("/")
        if route == "/":
            relative = "home.md"
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or path.suffix != ".md":
            raise ValueError(f"Invalid sidebar page: {route}")
        safe_path(SOURCE / relative)
        pages[route] = relative
    if not pages:
        raise ValueError("The sidebar must list at least one page")
    return pages


def publication_pages() -> dict[str, str]:
    """Publish the sidebar and the pages linked directly from the earlier Overview."""
    pages = sidebar_pages()
    for directory, names in (("guides", OVERVIEW_GUIDES), ("docs", OVERVIEW_REFERENCES)):
        for name in names:
            relative = (Path(directory) / (name + ".md")).as_posix()
            pages["/" + relative] = relative
    return pages


def rewrite_unpublished_links(content: str, document: str, published: set[str]) -> str:
    """Send references outside the retained page inventory to repository files."""
    def rewrite(match: re.Match[str]) -> str:
        label, href = match.groups()
        url = urlsplit(href)
        if url.scheme or url.netloc or not url.path:
            return match.group(0)
        target = posixpath.normpath(
            url.path.lstrip("/") if url.path.startswith("/")
            else posixpath.join(posixpath.dirname(document), url.path)
        )
        if target in published or target.startswith("assets/"):
            return match.group(0)
        if not target.endswith(".md") and not (ROOT / target).is_file():
            return match.group(0)
        if target == "repository.md":
            target = "README.md"
        if target.startswith(("guides/", "../")):
            return label
        suffix = "#" + url.fragment if url.fragment else ""
        return f"[{label}]({REPOSITORY_FILES}{target}{suffix})"

    return MARKDOWN_LINK.sub(rewrite, content)


def export() -> Path:
    safe_path(OUTPUT_PARENT)
    OUTPUT_PARENT.mkdir(parents=True, exist_ok=True)
    site = OUTPUT_PARENT / "site"
    staging = OUTPUT_PARENT / "staging"
    # Preserve unmarked output instead of deleting contents we cannot identify as ours.
    for path in (site, staging):
        safe_path(path)
        if path.exists():
            if not path.is_dir():
                raise ValueError(f"Output path is not a directory: {path}")
            marker = safe_path(path / MARKER)
            if not marker.is_file() or marker.read_text() != OWNER:
                backup = OUTPUT_PARENT / f"preserved-{path.name}-{time.time_ns()}"
                safe_path(backup)
                if backup.exists():
                    raise ValueError(f"Output backup already exists: {backup}")
                path.rename(backup)
                print(
                    "Preserved unmarked output at "
                    f"{backup.relative_to(ROOT).as_posix()}/", flush=True,
                )
    remove_output(staging)
    staging.mkdir()
    (staging / MARKER).write_text(OWNER, encoding="utf-8")
    (staging / ".nojekyll").touch()

    pages = publication_pages()
    documents = set(pages.values())
    shell_files = {"index.html", "home.md", "404.md", "_sidebar.md", "_navbar.md", "_coverpage.md"}
    for name in sorted(documents | shell_files):
        origin = ROOT if name.startswith("docs/") else SOURCE
        copy_file(origin / name, staging / name)
        if name.endswith(".md"):
            destination = staging / name
            destination.write_text(
                rewrite_unpublished_links(
                    destination.read_text(encoding="utf-8"), name, documents | shell_files,
                ), encoding="utf-8",
            )
    # An explicit asset inventory prevents stray private files in assets from being published.
    asset_paths = {
        "assets/portal.css", "assets/portal.js", "assets/theme.js",
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

    search_paths = {"en": list(pages)}
    (staging / "assets" / "search-paths.js").write_text(
        "window.portalSearchPaths = " + json.dumps(search_paths, indent=2) + ";\n",
        encoding="utf-8",
    )

    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    (staging / "export-manifest.json").write_text(
        json.dumps({
            "revision": revision,
            "content": "Current working-tree contents; revision is a reference, not acceptance.",
            "documents": sorted(
                name if name.startswith("docs/") else "src/redmine_mcp_docs/" + name
                for name in documents
            ), "references": [],
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
    paths = {ROOT / name for name in manifest["documents"]}
    paths.update(
        SOURCE / name for name in
        ("index.html", "home.md", "404.md", "_sidebar.md", "_navbar.md", "_coverpage.md")
    )
    for directory, pattern in (("guides", "*.md"), ("assets", "*")):
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
