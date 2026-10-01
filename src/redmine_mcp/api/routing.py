"""Normalize FastAPI route contracts, including lazy included-router contexts."""

from dataclasses import dataclass

from fastapi import FastAPI, routing
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute


@dataclass(frozen=True)
class RouteContract:
    operation_id: str | None
    path: str
    methods: frozenset[str]
    publishes_response: bool
    dependant: Dependant


def route_contracts(app: FastAPI) -> list[RouteContract]:
    # Recent FastAPI versions use route contexts; older versions flatten routes.
    iterator = getattr(routing, "iter_route_contexts", None)
    contexts = iterator(app.routes) if callable(iterator) else app.routes
    contracts: list[RouteContract] = []
    for context in contexts:
        original = getattr(context, "original_route", context)
        if not isinstance(original, APIRoute):
            continue
        contracts.append(
            RouteContract(
                operation_id=getattr(context, "operation_id", original.operation_id),
                path=getattr(context, "path", original.path),
                methods=frozenset(getattr(context, "methods", original.methods) or ()),
                publishes_response=getattr(context, "include_in_schema", original.include_in_schema)
                and getattr(context, "response_model", original.response_model) is not None,
                dependant=getattr(context, "dependant", original.dependant),
            )
        )
    return contracts
