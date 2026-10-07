"""Shared application contracts and validation helpers."""

from redmine_mcp.common.errors import ApplicationError, InvalidInputError
from redmine_mcp.common.pagination import Page, PageRequest
from redmine_mcp.common.validation import (
    NonnegativeInt,
    PositiveID,
    require_positive_id,
    validated_query,
)
from redmine_mcp.common.visibility import Collection, FieldObservation, Visibility

__all__ = [
    "ApplicationError",
    "Collection",
    "FieldObservation",
    "InvalidInputError",
    "NonnegativeInt",
    "Page",
    "PageRequest",
    "PositiveID",
    "Visibility",
    "require_positive_id",
    "validated_query",
]
