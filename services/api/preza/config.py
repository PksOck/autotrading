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
    telegram_chat_id: str | None = None
    app_base_url: str = "http://127.0.0.1:3000"

    status_timeout_s: float = Field(default=2.0, gt=0)

    base_currency: str = "EUR"
    bars_lookback_days: int = Field(default=800, gt=30)
    yahoo_enabled: bool = True
    stooq_enabled: bool = True

    rss_enabled: bool = True
    finnhub_api_key: str | None = None
    sec_edgar_user_agent: str | None = None
    radar_signal_threshold: float = Field(default=0.6, ge=0, le=1)
    radar_notify_threshold: float = Field(default=0.7, ge=0, le=1)

    benchmark_symbol: str = "SPY"  # entries (move vs market) and signal outcomes (alpha)

    # Deep analysis (M4, services/agents): LiteLLM roles for TradingAgents' two tiers.
    deep_quick_role: str = "cloud-quick"
    deep_deep_role: str = "cloud-deep"
    deep_debate_rounds: int = Field(default=1, ge=1, le=3)
    deep_daily_limit: int = Field(default=6, ge=0)  # 0 = no limit
    agents_home: str = "/data/agents"  # checkpoints, memory log and run logs


@lru_cache
def get_settings() -> Settings:
    return Settings()
