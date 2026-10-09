"""Restore canonical REST validation before MCP discovery and SDK caching."""

from copy import deepcopy
from http import HTTPMethod
from typing import Any

from mcp.types import Tool

SCHEMA_CONTRACT_ERROR = "MCP input schema does not match the REST contract"
SUPPORTED_HTTP_METHODS = frozenset(
    {
        HTTPMethod.GET,
        HTTPMethod.POST,
        HTTPMethod.PUT,
        HTTPMethod.PATCH,
        HTTPMethod.DELETE,
    }
)


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(SCHEMA_CONTRACT_ERROR)
    return value


class _References:
    """Keep local references in tool-owned definitions, including cycles."""

    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document
        self.definitions: dict[str, Any] = {}
        self.names: dict[str, str] = {}

    def target(self, reference: Any) -> dict[str, Any]:
        if not isinstance(reference, str) or not reference.startswith("#/"):
            raise ValueError(SCHEMA_CONTRACT_ERROR)
        value = self.document
        for part in reference[2:].split("/"):
            key = part.replace("~1", "/").replace("~0", "~")
            value = _object(value.get(key))
        return value

    def expand(self, value: Any) -> dict[str, Any]:
        """Expand object wrappers only; recursive property references stay local."""
        node = _object(value)
        seen: set[str] = set()
        while "$ref" in node:
            reference = node["$ref"]
            if not isinstance(reference, str) or reference in seen:
                raise ValueError(SCHEMA_CONTRACT_ERROR)
            seen.add(reference)
            node = {**self.target(reference), **{k: v for k, v in node.items() if k != "$ref"}}
        return node

    def copy(self, value: Any) -> Any:
        if isinstance(value, list):
            return [self.copy(item) for item in value]
        if not isinstance(value, dict):
            return deepcopy(value)
        # Instance-valued annotations may themselves contain a literal "$ref" key.
        literals = {"default", "const", "enum", "examples", "example"}
        result = {
            key: deepcopy(item) if key in literals else self.copy(item)
            for key, item in value.items()
            if key != "$ref"
        }
        if "$ref" in value:
            reference = value["$ref"]
            target = self.target(reference)
            if reference not in self.names:
                name = f"schema_{len(self.names)}"
                self.names[reference] = name
                # Reserve before visiting children so a recursive reference terminates.
                self.definitions[name] = {}
                self.definitions[name] = self.copy(target)
            result["$ref"] = f"#/$defs/{self.names[reference]}"
        return result


def _properties(
    operation: dict[str, Any], references: _References
) -> tuple[dict[str, Any], list[str]]:
    properties: dict[str, Any] = {}
    required: list[str] = []

    def add(name: Any, schema: Any, mandatory: bool) -> None:
        if not isinstance(name, str) or name in properties:
            raise ValueError(SCHEMA_CONTRACT_ERROR)
        properties[name] = references.copy(_object(schema))
        if mandatory:
            required.append(name)

    for value in operation.get("parameters", []):
        parameter = references.expand(value)
        if parameter.get("in") not in {"path", "query"}:
            continue
        schema = dict(_object(parameter.get("schema")))
        if "description" in parameter:
            schema["description"] = parameter["description"]
        add(parameter.get("name"), schema, parameter.get("required", False))
    if "requestBody" in operation:
        body = references.expand(operation["requestBody"])
        content = _object(body.get("content"))
        media = _object(content.get("application/json"))
        schema = references.expand(media.get("schema"))
        for name, value in _object(schema.get("properties")).items():
            add(name, value, name in schema.get("required", []))
    return properties, required


def repair_input_schemas(tools: list[Tool], document: dict[str, Any]) -> None:
    """Replace converted validation with route schemas, retaining root policy."""
    operations: dict[str, dict[str, Any]] = {}
    for path in _object(document.get("paths")).values():
        for method, operation in _object(path).items():
            if not isinstance(method, str):
                continue
            try:
                http_method = HTTPMethod(method.upper())
            except ValueError:
                continue
            if http_method not in SUPPORTED_HTTP_METHODS:
                continue
            operation = _object(operation)
            name = operation.get("operationId")
            if isinstance(name, str):
                if name in operations:
                    raise ValueError(SCHEMA_CONTRACT_ERROR)
                operations[name] = operation
    repaired: list[tuple[Tool, dict[str, Any]]] = []
    for tool in tools:
        if tool.name not in operations:
            raise ValueError(SCHEMA_CONTRACT_ERROR)
        references = _References(document)
        properties, required = _properties(operations[tool.name], references)
        generated = _object(tool.inputSchema.get("properties"))
        if properties.keys() != generated.keys():
            raise ValueError(SCHEMA_CONTRACT_ERROR)
        for name, schema in properties.items():
            # Adapter display titles do not affect validation; canonical titles win.
            if "title" not in schema and "title" in _object(generated[name]):
                schema["title"] = generated[name]["title"]
        result = deepcopy(tool.inputSchema)
        result["properties"] = properties
        result.pop("required", None)
        result.pop("$defs", None)
        if required:
            result["required"] = required
        if references.definitions:
            result["$defs"] = references.definitions
        repaired.append((tool, result))
    # Do not publish a partially repaired catalog if any tool fails matching.
    for tool, schema in repaired:
        tool.inputSchema = schema
