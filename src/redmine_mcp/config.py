from typing import Literal

from pydantic import Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from redmine_mcp.constants import runtime as runtime_text


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    redmine_url: HttpUrl
    redmine_write_enabled: bool = False
    redmine_timeout_seconds: float = Field(default=20, gt=0, allow_inf_nan=False)
    redmine_connect_timeout_seconds: float = Field(default=5, gt=0, allow_inf_nan=False)
    redmine_pool_timeout_seconds: float = Field(default=5, gt=0, allow_inf_nan=False)
    redmine_request_deadline_seconds: float = Field(default=60, gt=0, allow_inf_nan=False)
    redmine_max_response_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
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
        return self
