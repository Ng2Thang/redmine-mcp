"""Acquire pinned browser assets. This maintenance command requires Internet access."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import urlopen

VENDOR = Path(__file__).resolve().parents[1] / "assets" / "vendor"
PACKAGES = {
    "docsify": "4.13.1", "docsify-themeable": "0.9.0",
    "mermaid": "11.12.0", "prismjs": "1.29.0",
}
LANGUAGES = ("bash", "python", "json", "yaml", "toml", "docker", "diff", "ini")


def download(url: str) -> bytes:
    with urlopen(url, timeout=120) as response:
        return response.read()


def main() -> None:
    records: list[dict[str, object]] = []
    for name, version in PACKAGES.items():
        metadata = json.loads(download(f"https://registry.npmjs.org/{name}/{version}"))
        archive = download(metadata["dist"]["tarball"])
        integrity = metadata["dist"]["integrity"]
        algorithm, encoded = integrity.split("-", 1)
        actual = base64.b64encode(hashlib.new(algorithm, archive).digest()).decode()
        if actual != encoded:
            raise ValueError(f"Package integrity mismatch: {name}")
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
            files = {member.name: member for member in package.getmembers() if member.isfile()}
            if name == "docsify":
                selected = [
                    "lib/docsify.min.js", "lib/plugins/search.min.js",
                ]
            elif name == "docsify-themeable":
                selected = ["dist/css/theme-simple.css", "dist/js/docsify-themeable.min.js"]
            elif name == "prismjs":
                selected = [f"components/prism-{language}.min.js" for language in LANGUAGES]
            else:
                selected = ["dist/mermaid.min.js"]
            # Keep every license/notice distributed with the browser package.
            selected += [
                path.removeprefix("package/") for path in files
                if re.search(r"(^|/)(license|licence|notice|copying)(\.|$)", path, re.I)
                or path.lower().endswith(".license.txt")
            ]
            package_files: list[dict[str, str]] = []
            for relative in sorted(set(selected)):
                member = files.get(f"package/{relative}")
                if member is None:
                    raise ValueError(f"Missing required asset: {name}/{relative}")
                stream = package.extractfile(member)
                if stream is None:
                    raise ValueError(f"Unreadable asset: {name}/{relative}")
                content = stream.read()
                destination = VENDOR / name / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                package_files.append({
                    "path": destination.relative_to(VENDOR).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                })
            license_path = VENDOR / name / "LICENSE"
            if not license_path.exists():
                source = (
                    f"https://raw.githubusercontent.com/mermaid-js/mermaid/"
                    f"mermaid%40{version}/LICENSE"
                )
                content = download(source)
                license_path.write_bytes(content)
                package_files.append({
                    "path": license_path.relative_to(VENDOR).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                })
            records.append({
                "package": name, "version": version,
                "tarball": metadata["dist"]["tarball"], "integrity": integrity,
                "files": package_files,
            })
            print(f"Vendored {name} {version}: {len(package_files)} files")
    (VENDOR / "manifest.json").write_text(
        json.dumps({
            "packages": records,
            "modifications": [],
        }, indent=2) + "\n", encoding="utf-8",
    )


if __name__ == "__main__":
    main()
