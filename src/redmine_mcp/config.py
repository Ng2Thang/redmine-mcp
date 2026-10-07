import re
from typing import Literal

from pydantic import Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from redmine_mcp.auth.policy import WRITE_OPERATIONS
from redmine_mcp.common.read_budget import MEMBERSHIP_BATCH_DEFAULTS
from redmine_mcp.constants import runtime as runtime_text


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    redmine_url: HttpUrl
    redmine_public_url: HttpUrl | None = None
    redmine_max_concurrent_requests: int = Field(default=50, ge=1)
    redmine_admission_timeout_seconds: float = Field(default=30, gt=0, allow_inf_nan=False)
    redmine_max_query_pages: int = Field(default=10, ge=1)
    redmine_read_operation_max_requests: int = Field(default=30, ge=1)
    redmine_read_operation_deadline_seconds: float = Field(default=90, gt=0, allow_inf_nan=False)
    redmine_read_operation_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    redmine_membership_batch_max_requests: int = Field(
        default=MEMBERSHIP_BATCH_DEFAULTS.max_requests, ge=1
    )
    redmine_membership_batch_max_read_bytes: int = Field(
        default=MEMBERSHIP_BATCH_DEFAULTS.max_bytes, ge=1
    )
    redmine_membership_batch_deadline_seconds: float = Field(
        default=MEMBERSHIP_BATCH_DEFAULTS.deadline_seconds, gt=0, allow_inf_nan=False
    )
    redmine_write_enabled: bool = False
    redmine_writer_auth_mode: Literal["pinned_key", "personal_key"] = "pinned_key"
    redmine_writer_user_ids: str = ""
    redmine_writer_operations: str = ""
    redmine_writer_key_sha256: str = Field(default="", repr=False)
    redmine_timeout_seconds: float = Field(default=20, gt=0, allow_inf_nan=False)
    redmine_connect_timeout_seconds: float = Field(default=5, gt=0, allow_inf_nan=False)
    redmine_pool_timeout_seconds: float = Field(default=5, gt=0, allow_inf_nan=False)
    redmine_request_deadline_seconds: float = Field(default=60, gt=0, allow_inf_nan=False)
    redmine_max_response_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    redmine_max_binary_bytes: int = Field(default=5 * 1024 * 1024, ge=1)
    redmine_max_request_body_bytes: int | None = Field(default=None, ge=1)
    redmine_max_connections: int = Field(default=100, ge=1)
    redmine_max_keepalive_connections: int = Field(default=20, ge=0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("redmine_public_url", mode="before")
    @classmethod
    def empty_public_url(cls, value: object) -> object:
        return None if value == "" else value

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
        if self.redmine_public_url is not None:
            if self.redmine_public_url.username or self.redmine_public_url.password:
                raise ValueError(runtime_text.URL_CONTAINS_CREDENTIALS)
            if (
                self.redmine_public_url.query is not None
                or self.redmine_public_url.fragment is not None
            ):
                raise ValueError(runtime_text.URL_CONTAINS_QUERY_OR_FRAGMENT)
        if self.redmine_write_enabled:
            user_ids = [part.strip() for part in self.redmine_writer_user_ids.split(",")]
            operations = [part.strip() for part in self.redmine_writer_operations.split(",")]
            if (
                self.redmine_writer_auth_mode == "pinned_key" or self.redmine_writer_user_ids
            ) and any(not re.fullmatch(r"[1-9][0-9]*", part) for part in user_ids):
                raise ValueError(runtime_text.WRITER_USER_IDS_REQUIRED)
            if (
                any(not re.fullmatch(r"[a-z][a-z0-9_]*", part) for part in operations if part)
                or (self.redmine_writer_operations and any(not part for part in operations))
                or ("allowed_all" in operations and operations != ["allowed_all"])
            ):
                raise ValueError(runtime_text.WRITER_OPERATIONS_REQUIRED)
            if self.redmine_writer_auth_mode == "pinned_key" and not re.fullmatch(
                r"[0-9a-f]{64}", self.redmine_writer_key_sha256
            ):
                raise ValueError(runtime_text.WRITER_KEY_HASH_REQUIRED)
        if self.redmine_writer_auth_mode == "personal_key" and self.redmine_writer_key_sha256:
            raise ValueError(runtime_text.PERSONAL_WRITER_HASH_FORBIDDEN)
        return self

    @property
    def effective_max_request_body_bytes(self) -> int:
        if self.redmine_max_request_body_bytes is not None:
            return self.redmine_max_request_body_bytes
        return max(
            self.redmine_max_response_bytes,
            4 * ((self.redmine_max_binary_bytes + 2) // 3) + 65536,
        )

    @property
    def personal_writer(self) -> bool:
        return self.redmine_write_enabled and self.redmine_writer_auth_mode == "personal_key"

    @property
    def writer_user_ids(self) -> frozenset[int]:
        return frozenset(
            int(part.strip()) for part in self.redmine_writer_user_ids.split(",") if part.strip()
        )

    @property
    def writer_operations(self) -> frozenset[str]:
        if self.redmine_writer_operations.strip() == "allowed_all":
            return frozenset(WRITE_OPERATIONS)
        return frozenset(
            part.strip() for part in self.redmine_writer_operations.split(",") if part.strip()
        )
