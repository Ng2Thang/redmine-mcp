from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from redmine_mcp.common.errors import ApplicationError
from redmine_mcp.common.pagination import Page
from redmine_mcp.common.visibility import Collection, Visibility
from redmine_mcp.integrations.redmine.visibility import observe_fields

T = TypeVar("T", bound=BaseModel)


def require_observable_fields(model: type[BaseModel], fields: Sequence[str]) -> None:
    unknown = set(fields).difference(model.model_fields)
    if unknown:
        raise ValueError(
            f"Observable fields are not declared on {model.__name__}: {sorted(unknown)}"
        )


def item[T: BaseModel](model: type[T], value: Any) -> T:
    try:
        if not isinstance(value, dict):
            raise ValueError
        return model.model_validate(value)
    except (ValidationError, ValueError):
        raise ApplicationError("upstream_response", "Unexpected Redmine data", 502) from None


def visible_item[T: BaseModel](
    model: type[T],
    value: Any,
    *,
    observed_fields: Sequence[str] = (),
    requested_fields: Sequence[str] = (),
    unrequested_fields: Sequence[str] = (),
) -> T:
    require_observable_fields(model, (*observed_fields, *requested_fields, *unrequested_fields))
    if "visibility" not in model.model_fields:
        raise ValueError(f"{model.__name__} has no visibility field")
    if not isinstance(value, dict):
        return item(model, value)
    observations = observe_fields(value, observed_fields)
    observations.extend(observe_fields(value, requested_fields))
    observations.extend(observe_fields(value, unrequested_fields, state="not_requested"))
    return item(model, {**value, "visibility": Visibility(observations=observations)})


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
    model: type[T],
    data: dict[str, Any],
    key: str,
    limit: int,
    offset: int,
    *,
    observed_fields: tuple[str, ...] = (),
) -> Page[T]:
    require_observable_fields(model, observed_fields)
    try:
        values = data[key]
        if not isinstance(values, list):
            raise TypeError
        return Page(
            items=[item(model, entry) for entry in values],
            total=data["total_count"],
            limit=limit,
            offset=offset,
            visibility=Visibility(
                observations=[
                    observation
                    for index, entry in enumerate(values)
                    for observation in observe_fields(
                        entry, observed_fields, prefix=f"/items/{index}"
                    )
                ]
            ),
        )
    except (KeyError, TypeError, ValidationError):
        raise ApplicationError("upstream_response", "Unexpected Redmine page", 502) from None


def wrapped_collection[T: BaseModel](
    model: type[T],
    data: dict[str, Any],
    key: str,
    *,
    complete: bool = False,
    observed_fields: tuple[str, ...] = (),
) -> Collection[T]:
    require_observable_fields(model, observed_fields)
    values = complete_collection(model, data, key) if complete else collection(model, data, key)
    raw_items = data[key]
    return Collection(
        items=values,
        visibility=Visibility(
            observations=[
                observation
                for index, entry in enumerate(raw_items)
                for observation in observe_fields(entry, observed_fields, prefix=f"/items/{index}")
            ]
        ),
    )
