from collections.abc import Mapping, Sequence
from typing import Any, Literal

from redmine_mcp.common.visibility import FieldObservation


def observe_fields(
    source: Mapping[str, Any],
    fields: Sequence[str],
    *,
    prefix: str = "",
    state: Literal["not_returned", "not_requested"] = "not_returned",
) -> list[FieldObservation]:
    """Describe expected fields absent from an upstream object, without guessing why."""
    return [
        FieldObservation(path=f"{prefix}/{name.replace('~', '~0').replace('/', '~1')}", state=state)
        for name in fields
        if name not in source
    ]
