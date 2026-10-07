"""SCHEMA-022-003: canonical unions, constraints, references and atomic repair."""

from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator
from mcp.types import Tool

from redmine_mcp.mcp.schema import SCHEMA_CONTRACT_ERROR, repair_input_schemas


def catalog(schema):
    document = {
        "paths": {
            "/example": {
                "post": {
                    "operationId": "example",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"value": schema},
                                    "required": ["value"],
                                }
                            }
                        }
                    },
                }
            }
        }
    }
    tool = Tool(
        name="example",
        inputSchema={
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "additionalProperties": False,
        },
    )
    return document, tool


def test_canonical_union_and_nested_constraints_replace_adapter_type():
    schema = {
        "anyOf": [
            {"type": "integer", "exclusiveMinimum": 0},
            {"type": "string", "enum": ["me"]},
            {"type": "null"},
        ]
    }
    document, tool = catalog(schema)
    repair_input_schemas([tool], document)
    assert tool.inputSchema["properties"]["value"] == schema
    assert tool.inputSchema["additionalProperties"] is False
    validator = Draft202012Validator(tool.inputSchema)
    for value in (1, "me", None):
        assert validator.is_valid({"value": value})
    for value in (0, -1, True, "1", "other"):
        assert not validator.is_valid({"value": value})


def test_authored_type_and_recursive_references_survive_without_expansion():
    document, tool = catalog({"$ref": "#/components/schemas/Node"})
    document["components"] = {
        "schemas": {
            "Node": {
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "integer", "minimum": 1},
                    "children": {
                        "type": "array",
                        "maxItems": 2,
                        "items": {"$ref": "#/components/schemas/Node"},
                    },
                },
                "examples": [{"$ref": "literal-instance-value"}],
            }
        }
    }
    repair_input_schemas([tool], document)
    assert len(tool.inputSchema["$defs"]) == 1
    validator = Draft202012Validator(tool.inputSchema)
    assert validator.is_valid({"value": {"id": 1, "children": [{"id": 2}]}})
    assert not validator.is_valid({"value": {"id": 1, "children": [{"id": 0}]}})
    assert tool.inputSchema["$defs"]["schema_0"]["examples"] == [{"$ref": "literal-instance-value"}]


@pytest.mark.parametrize("fault", ["missing", "duplicate", "remote_ref", "property"])
def test_invalid_contract_fails_atomically(fault):
    document, tool = catalog({"type": "integer"})
    before = deepcopy(tool.inputSchema)
    second = tool.model_copy(deep=True)
    if fault == "missing":
        second.name = "absent"
    elif fault == "duplicate":
        document["paths"]["/duplicate"] = deepcopy(document["paths"]["/example"])
    elif fault == "remote_ref":
        document["paths"]["/example"]["post"]["requestBody"]["content"]["application/json"][
            "schema"
        ]["properties"]["value"] = {"$ref": "https://invalid/schema"}
    else:
        second.inputSchema["properties"] = {}
    with pytest.raises(ValueError, match=SCHEMA_CONTRACT_ERROR):
        repair_input_schemas([tool, second], document)
    assert tool.inputSchema == before
