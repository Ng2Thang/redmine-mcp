"""Sentinel parsing preserves explicit/empty configuration and catalog validation."""

import pytest
from pydantic import ValidationError

from redmine_mcp.auth import WRITE_OPERATIONS
from redmine_mcp.config import Settings
from redmine_mcp.mcp.catalog import writer_catalog


@pytest.mark.parametrize("enabled", [False, True])
def test_retired_writer_admission_environment_is_ignored(
    monkeypatch: pytest.MonkeyPatch, enabled: bool
) -> None:
    monkeypatch.setenv("REDMINE_WRITER_AUTH_MODE", "retired-mode")
    monkeypatch.setenv("REDMINE_WRITER_USER_IDS", "retired-user-list")
    monkeypatch.setenv("REDMINE_WRITER_KEY_SHA256", "retired-key-hash")
    settings = Settings(
        _env_file=None,
        redmine_url="http://redmine.invalid",
        redmine_write_enabled=enabled,
        redmine_writer_operations="create_issue",
    )
    assert settings.redmine_write_enabled is enabled
    assert settings.writer_operations == frozenset({"create_issue"})


@pytest.mark.parametrize("value", ["allowed_all", " allowed_all ", "\tallowed_all\n"])
def test_standalone_sentinel_expands_current_registered_writers(value: str) -> None:
    settings = Settings(
        _env_file=None,
        redmine_url="http://redmine.invalid",
        redmine_write_enabled=True,
        redmine_writer_operations=value,
    )
    assert settings.writer_operations == frozenset(WRITE_OPERATIONS)
    assert set(writer_catalog(settings.writer_operations)) >= set(WRITE_OPERATIONS)


@pytest.mark.parametrize(
    "value",
    [
        "allowed_all,create_issue",
        "create_issue,allowed_all",
        "allowed_all,allowed_all",
        "allowed_all,",
        "Allowed_all",
    ],
)
def test_invalid_sentinel_forms_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            redmine_url="http://redmine.invalid",
            redmine_write_enabled=True,
            redmine_writer_operations=value,
        )


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", frozenset()),
        (" create_issue , update_issue ", frozenset({"create_issue", "update_issue"})),
    ],
)
def test_empty_and_explicit_csv_compatible(value: str, expected: frozenset[str]) -> None:
    settings = Settings(
        _env_file=None,
        redmine_url="http://redmine.invalid",
        redmine_write_enabled=True,
        redmine_writer_operations=value,
    )
    assert settings.writer_operations == expected


def test_unknown_operation_rejected_by_catalog_validation() -> None:
    settings = Settings(
        _env_file=None,
        redmine_url="http://redmine.invalid",
        redmine_write_enabled=True,
        redmine_writer_operations="unknown_operation",
    )
    with pytest.raises(ValueError):
        writer_catalog(settings.writer_operations)
