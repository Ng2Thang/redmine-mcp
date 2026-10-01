"""Public application configuration and factory."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from redmine_mcp.config import Settings

if TYPE_CHECKING:
    from redmine_mcp.app import create_app as create_app

__all__ = ["Settings", "create_app"]


def __getattr__(name: str) -> Callable[..., object]:
    if name == "create_app":
        # Domain imports must not initialize HTTP adapters or dependency composition.
        from redmine_mcp.app import create_app

        globals()[name] = create_app
        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
