from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from redmine_mcp.common.errors import ApplicationError
from redmine_mcp.common.pagination import Page

T = TypeVar("T", bound=BaseModel)


def item[T: BaseModel](model: type[T], value: Any) -> T:
    try:
        return model.model_validate(value)
    except ValidationError:
        raise ApplicationError("upstream_response", "Unexpected Redmine data", 502) from None


def collection[T: BaseModel](model: type[T], data: dict[str, Any], key: str) -> list[T]:
    try:
        values = data[key]
        if not isinstance(values, list):
            raise TypeError
        return [item(model, value) for value in values]
    except (KeyError, TypeError):
        raise ApplicationError("upstream_response", "Unexpected Redmine data", 502) from None


def complete_collection[T: BaseModel](model: type[T], data: dict[str, Any], key: str) -> list[T]:
    values = collection(model, data, key)
    count = data.get("total_count")
    if type(count) is not int or count < 0 or count != len(values):
        raise ApplicationError("upstream_response", "Unexpected Redmine data", 502)
    return values


def page[T: BaseModel](
    model: type[T], data: dict[str, Any], key: str, limit: int, offset: int
) -> Page[T]:
    try:
        return Page(
            items=[item(model, entry) for entry in data[key]],
            total=data["total_count"],
            limit=limit,
            offset=offset,
        )
    except (KeyError, TypeError, ValidationError):
        raise ApplicationError("upstream_response", "Unexpected Redmine page", 502) from None
