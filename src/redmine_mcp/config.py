import re
from typing import Literal

from pydantic import Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from redmine_mcp.constants import runtime as runtime_text


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    redmine_url: HttpUrl
    redmine_write_enabled: bool = False
    redmine_writer_user_ids: str = ""
    redmine_writer_operations: str = ""
    redmine_writer_key_sha256: str = Field(default="", repr=False)
    redmine_timeout_seconds: float = Field(default=20, gt=0, allow_inf_nan=False)
    redmine_connect_timeout_seconds: float = Field(default=5, gt=0, allow_inf_nan=False)
    redmine_pool_timeout_seconds: float = Field(default=5, gt=0, allow_inf_nan=False)
    redmine_request_deadline_seconds: float = Field(default=60, gt=0, allow_inf_nan=False)
    redmine_max_response_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    redmine_max_binary_bytes: int = Field(default=5 * 1024 * 1024, ge=1)
    redmine_max_connections: int = Field(default=100, ge=1)
    redmine_max_keepalive_connections: int = Field(default=20, ge=0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_transport(self) -> "Settings":
        if self.redmine_max_keepalive_connections > self.redmine_max_connections:
            raise ValueError(runtime_text.INVALID_KEEPALIVE_LIMIT)
        if self.redmine_url.username or self.redmine_url.password:
            raise ValueError(runtime_text.URL_CONTAINS_CREDENTIALS)
        if self.redmine_url.query is not None or self.redmine_url.fragment is not None:
            raise ValueError(runtime_text.URL_CONTAINS_QUERY_OR_FRAGMENT)
        if self.redmine_write_enabled:
            user_ids = [part.strip() for part in self.redmine_writer_user_ids.split(",")]
            operations = [part.strip() for part in self.redmine_writer_operations.split(",")]
            if not user_ids or any(not re.fullmatch(r"[1-9][0-9]*", part) for part in user_ids):
                raise ValueError(runtime_text.WRITER_USER_IDS_REQUIRED)
            if any(not re.fullmatch(r"[a-z][a-z0-9_]*", part) for part in operations if part) or (
                self.redmine_writer_operations and any(not part for part in operations)
            ):
                raise ValueError(runtime_text.WRITER_OPERATIONS_REQUIRED)
            if not re.fullmatch(r"[0-9a-f]{64}", self.redmine_writer_key_sha256):
                raise ValueError(runtime_text.WRITER_KEY_HASH_REQUIRED)
        return self

    @property
    def writer_user_ids(self) -> frozenset[int]:
        return frozenset(
            int(part.strip()) for part in self.redmine_writer_user_ids.split(",") if part.strip()
        )

    @property
    def writer_operations(self) -> frozenset[str]:
        return frozenset(
            part.strip() for part in self.redmine_writer_operations.split(",") if part.strip()
        )
