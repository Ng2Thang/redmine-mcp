"""Localhost application factory for supplemental Inspector and browser checks."""

from typing import Any

from redmine_mcp.app import create_app as application
from redmine_mcp.auth import WRITE_OPERATIONS
from redmine_mcp.config import Settings
from tests.e2e.conftest import preflight


def create_app() -> Any:
    manifest = preflight()
    return application(
        Settings(
            _env_file=None,
            redmine_url="http://127.0.0.1:3001",
            redmine_write_enabled=True,
            redmine_writer_auth_mode="personal_key",
            redmine_writer_user_ids=",".join(
                str(row["id"]) for name, row in manifest["users"].items() if name != "admin"
            ),
            redmine_writer_operations=",".join(WRITE_OPERATIONS),
        )
    )
