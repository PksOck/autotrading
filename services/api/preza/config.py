"""Runtime configuration, read from environment variables (see .env.example)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    default_locale: str = "sl"

    database_url: str = "postgresql+asyncpg://preza:preza@localhost:5432/preza"
    redis_url: str = "redis://localhost:6379/0"

    litellm_base_url: str = "http://localhost:4000"
    litellm_master_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    ib_gateway_enabled: bool = False
    ib_gateway_host: str = "localhost"
    ib_gateway_port: int = 4001
    ibkr_flex_token: str | None = None
    ibkr_flex_query_id: str | None = None

    telegram_bot_token: str | None = None

    status_timeout_s: float = Field(default=2.0, gt=0)

    base_currency: str = "EUR"
    bars_lookback_days: int = Field(default=800, gt=30)
    yahoo_enabled: bool = True
    stooq_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
