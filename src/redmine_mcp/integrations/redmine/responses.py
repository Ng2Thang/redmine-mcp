"""Validate upstream envelopes before feature-specific model conversion."""

from dataclasses import dataclass
from typing import Any

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError


def response_object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ApplicationError(
            "upstream_response", "Unexpected Redmine data", http_status.HTTP_502_BAD_GATEWAY
        )
    return value


def response_items(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    values = data.get(key)
    if not isinstance(values, list):
        raise ApplicationError(
            "upstream_response", "Unexpected Redmine data", http_status.HTTP_502_BAD_GATEWAY
        )
    return [response_object(value) for value in values]


def resource_object(value: Any, expected_id: int) -> dict[str, Any]:
    resource = response_object(value)
    if type(resource.get("id")) is not int or resource["id"] != expected_id:
        raise ApplicationError(
            "upstream_response", "Unexpected Redmine data", http_status.HTTP_502_BAD_GATEWAY
        )
    return resource


def response_count(data: dict[str, Any]) -> int:
    count = data.get("total_count")
    if type(count) is not int or count < 0:
        raise ApplicationError(
            "upstream_response", "Unexpected Redmine page", http_status.HTTP_502_BAD_GATEWAY
        )
    return count


@dataclass(frozen=True)
class ResponsePage:
    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


def response_page(
    data: dict[str, Any],
    key: str,
    limit: int,
    offset: int,
    *,
    require_metadata: bool = False,
) -> ResponsePage:
    """Allow omitted echoes where supported; reject malformed or mismatched echoes.

    Counts and rows can change between upstream queries, so total_count is not
    used to infer that a short page is complete or that an offset is invalid.
    """
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or offset < 0:
        raise ApplicationError(
            "upstream_response", "Unexpected Redmine page", http_status.HTTP_502_BAD_GATEWAY
        )
    values = response_items(data, key)
    total = response_count(data)
    if len(values) > limit:
        raise ApplicationError(
            "upstream_response", "Unexpected Redmine page", http_status.HTTP_502_BAD_GATEWAY
        )
    for name, expected in (("limit", limit), ("offset", offset)):
        if name not in data and not require_metadata:
            continue
        actual = data.get(name)
        if type(actual) is not int or actual != expected:
            raise ApplicationError(
                "upstream_response", "Unexpected Redmine page", http_status.HTTP_502_BAD_GATEWAY
            )
    return ResponsePage(values, total, limit, offset)
