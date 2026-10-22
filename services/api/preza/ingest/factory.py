"""Builds the Radar's news sources from settings."""

from preza.config import Settings
from preza.ingest.base import NewsSource
from preza.ingest.edgar import EdgarSource
from preza.ingest.finnhub import FinnhubSource
from preza.ingest.rss import DEFAULT_FEEDS, RssSource


def build_sources(
    settings: Settings, symbols: list[str], cik_to_ticker: dict[str, str] | None
) -> list[NewsSource]:
    sources: list[NewsSource] = []
    if settings.rss_enabled:
        sources += [RssSource(name, url) for name, url in DEFAULT_FEEDS]
    if settings.finnhub_api_key and symbols:
        # Free tier: 60 calls/minute. Portfolio + watchlist stays well below that.
        sources.append(FinnhubSource(settings.finnhub_api_key, symbols[:50]))
    if settings.sec_edgar_user_agent:
        sources.append(EdgarSource(settings.sec_edgar_user_agent, cik_to_ticker=cik_to_ticker))
    return sources
