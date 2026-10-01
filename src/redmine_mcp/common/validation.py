from typing import Any

from pydantic import BaseModel, ValidationError

from redmine_mcp.common.errors import InvalidInputError
from redmine_mcp.constants import common as common_text


def require_positive_id(value: int, name: str) -> None:
    if type(value) is not int or value < 1:
        raise InvalidInputError(common_text.POSITIVE_INTEGER_REQUIRED.format(name=name))


def validated_query[T: BaseModel](model: type[T], values: dict[str, Any]) -> T:
    try:
        return model.model_validate(values)
    except ValidationError:
        # Do not carry caller input or Pydantic exception text into public errors/logs.
        raise InvalidInputError(common_text.INVALID_QUERY_PARAMETERS) from None
