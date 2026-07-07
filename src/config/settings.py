from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    bot_token: SecretStr = Field(default=SecretStr("CHANGE_ME"))
    database_url: str = Field(default="postgresql+asyncpg://bot:bot@postgres:5432/bot")
    redis_url: str = Field(default="redis://redis:6379/0")
    webhook_url: str | None = None
    rate_limit_per_minute: int = 30
    http_timeout_seconds: float = 20.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
