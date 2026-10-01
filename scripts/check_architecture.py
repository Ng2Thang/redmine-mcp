"""Check runtime import boundaries and cycles without importing application code."""

import ast
from importlib.util import resolve_name
from pathlib import Path

RUNTIME = Path(__file__).resolve().parents[1] / "src"


def module_name(path: Path) -> str:
    parts = list(path.relative_to(RUNTIME).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imports(path: Path, module: str) -> set[str]:
    names: set[str] = set()
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ""
            if node.level:
                name = resolve_name("." * node.level + name, package)
            # FastAPI reexports status from Starlette; importing only that namespace
            # does not introduce a framework API dependency into a domain module.
            if name != "fastapi" or any(alias.name != "status" for alias in node.names):
                names.add(name)
            names.update(f"{name}.{alias.name}" for alias in node.names)
    return names


def in_package(module: str, package: str) -> bool:
    return module == package or module.startswith(package + ".")


def export_aliases(files: dict[str, Path]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for module, path in files.items():
        if path.name != "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        public: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
            ):
                public = set(ast.literal_eval(node.value))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                origin = node.module or ""
                if node.level:
                    origin = resolve_name("." * node.level + origin, module)
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name in public:
                        aliases[f"{module}.{name}"] = f"{origin}.{alias.name}"
    return aliases


def resolve_export(target: str, aliases: dict[str, str]) -> str:
    visited: set[str] = set()
    while target in aliases and target not in visited:
        visited.add(target)
        target = aliases[target]
    return target


def forbidden(source: str, target: str) -> bool:
    if in_package(source, "redmine_mcp.constants"):
        # Constants are shared by every layer and must not pull in runtime code.
        return (
            in_package(target, "redmine_mcp")
            and not in_package(target, "redmine_mcp.constants")
            or any(
                in_package(target, name)
                for name in ("fastapi", "fastapi_mcp", "starlette", "httpx", "pydantic")
            )
        )
    if in_package(target, "fastapi.status"):
        return False
    domain = any(
        in_package(source, name) for name in ("redmine_mcp.common", "redmine_mcp.auth")
    ) or (
        in_package(source, "redmine_mcp.features")
        and bool(set(source.split(".")[2:]).intersection({"service", "ports", "models", "queries"}))
    )
    if domain and any(
        in_package(target, name)
        for name in (
            "fastapi",
            "fastapi_mcp",
            "starlette",
            "httpx",
            "redmine_mcp.api",
            "redmine_mcp.integrations",
            "redmine_mcp.mcp",
            "redmine_mcp.bootstrap",
            "redmine_mcp.app",
            "redmine_mcp.lifecycle",
        )
    ):
        return True
    if in_package(source, "redmine_mcp.common") and any(
        in_package(target, name) for name in ("redmine_mcp.auth", "redmine_mcp.features")
    ):
        return True
    if in_package(source, "redmine_mcp.auth") and in_package(target, "redmine_mcp.features"):
        return True
    feature_endpoint = in_package(target, "redmine_mcp.features") and bool(
        set(target.split(".")[2:]).intersection({"service", "router"})
    )
    if domain and in_package(target, "redmine_mcp.features") and "router" in target.split(".")[2:]:
        return True
    if in_package(source, "redmine_mcp.integrations"):
        return (
            any(
                in_package(target, name)
                for name in (
                    "redmine_mcp.api",
                    "redmine_mcp.mcp",
                    "redmine_mcp.bootstrap",
                    "redmine_mcp.app",
                    "redmine_mcp.lifecycle",
                )
            )
            or feature_endpoint
        )
    return in_package(source, "redmine_mcp.api") and in_package(target, "redmine_mcp.integrations")


def main() -> int:
    files = {module_name(path): path for path in sorted(RUNTIME.rglob("*.py"))}
    dependencies = {name: imports(path, name) for name, path in files.items()}
    aliases = export_aliases(files)
    errors = {
        f"Forbidden import: {source} -> {target}"
        for source, targets in dependencies.items()
        for target in targets
        if forbidden(source, resolve_export(target, aliases))
    }
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(module: str) -> None:
        if module in visiting:
            cycle = visiting[visiting.index(module) :] + [module]
            errors.add(f"Import cycle: {' -> '.join(cycle)}")
            return
        if module in visited:
            return
        visiting.append(module)
        for imported in sorted(dependencies[module]):
            target = resolve_export(imported, aliases)
            while target not in files and "." in target:
                target = target.rpartition(".")[0]
            if target in files and target != module:
                visit(target)
        visiting.pop()
        visited.add(module)

    for module in files:
        visit(module)
    for error in sorted(errors):
        print(error)
    if errors:
        return 1
    print(f"Architecture import boundaries and cycles passed ({len(files)} runtime modules).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
