from typing import Literal

from pydantic import BaseModel, Field


class FieldObservation(BaseModel):
    path: str
    state: Literal["not_returned", "not_requested"]


class Visibility(BaseModel):
    scope: Literal["shared_redmine_account"] = "shared_redmine_account"
    observations: list[FieldObservation] = Field(default_factory=list)


class Collection[T](BaseModel):
    items: list[T]
    visibility: Visibility = Field(default_factory=Visibility)
