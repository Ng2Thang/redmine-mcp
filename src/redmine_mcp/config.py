from pydantic import HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    redmine_url: HttpUrl
    redmine_api_key: SecretStr
    mcp_api_token: SecretStr
    redmine_timeout_seconds: float = 20
    log_level: str = "INFO"

    @field_validator("redmine_api_key", "mcp_api_token")
    @classmethod
    def nonempty_secret(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip() or value.get_secret_value().startswith("replace-"):
            raise ValueError("Configure a real local credential")
        return value

    @field_validator("redmine_timeout_seconds")
    @classmethod
    def positive_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Timeout must be positive")
        return value
