"""Localhost application factory for supplemental Inspector and browser checks."""

import json
from typing import Any

from redmine_mcp.app import create_app as application
from redmine_mcp.auth import WRITE_OPERATIONS
from redmine_mcp.config import Settings
from tests.e2e.conftest import preflight
from tools.testing.e2e_config import PROJECT, STATE, URL, VERSION


def create_app() -> Any:
    preflight()
    return application(
        Settings(
            _env_file=None,
            redmine_url=URL,
            redmine_write_enabled=True,
            redmine_writer_operations=",".join(WRITE_OPERATIONS),
        )
    )


def create_reader_app() -> Any:
    preflight()
    return application(Settings(_env_file=None, redmine_url=URL))


def create_allowed_all_app() -> Any:
    preflight()
    return application(
        Settings(
            _env_file=None,
            redmine_url=URL,
            redmine_write_enabled=True,
            redmine_writer_operations="allowed_all",
        )
    )


def create_time_entry_update_app() -> Any:
    preflight()
    path = STATE / "tool042-fixtures.json"
    fixture = json.loads(path.read_text())
    if (
        fixture.get("owner") != "tool-042"
        or fixture.get("version") != VERSION
        or fixture.get("project") != PROJECT
    ):
        raise ValueError("Unexpected TOOL-042 fixture ownership")
    return application(
        Settings(
            _env_file=None,
            redmine_url=URL,
            redmine_write_enabled=True,
            redmine_writer_operations="update_time_entry",
        )
    )


def create_time_entry_delete_app() -> Any:
    preflight()
    path = STATE / "tool043-fixtures.json"
    fixture = json.loads(path.read_text())
    if (
        fixture.get("owner") != "tool-043"
        or fixture.get("version") != VERSION
        or fixture.get("project") != PROJECT
    ):
        raise ValueError("Unexpected TOOL-043 fixture ownership")
    return application(
        Settings(
            _env_file=None,
            redmine_url=URL,
            redmine_write_enabled=True,
            redmine_writer_operations="delete_time_entry",
        )
    )
