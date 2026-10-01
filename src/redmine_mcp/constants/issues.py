"""Issues text constants; no runtime dependencies.

Templates use named str.format arguments; log templates use logging placeholders.
"""

from typing import Final

ISO_DATE_REQUIRED: Final[str] = "Expected an ISO calendar date"

JSON_NUMBER_REQUIRED: Final[str] = "Expected a JSON number"

RFC3339_TIMESTAMP_REQUIRED: Final[str] = "Expected an RFC 3339 timestamp with timezone"

PROJECT_REQUIRED_FOR_CATEGORY: Final[str] = "project_id is required with category_id"

PROJECT_REQUIRED_WITHOUT_SUBPROJECTS: Final[str] = (
    "project_id is required when include_subprojects is false"
)

INVALID_INCLUDE_SELECTION: Final[str] = "Invalid issue include selection"

__all__ = [
    "ISO_DATE_REQUIRED",
    "JSON_NUMBER_REQUIRED",
    "RFC3339_TIMESTAMP_REQUIRED",
    "PROJECT_REQUIRED_FOR_CATEGORY",
    "PROJECT_REQUIRED_WITHOUT_SUBPROJECTS",
    "INVALID_INCLUDE_SELECTION",
]
