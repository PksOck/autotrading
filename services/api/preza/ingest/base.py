"""News source contract (BL-040, BL-041). Each source returns NewsIn items newer than `since`."""

from datetime import datetime
from typing import Protocol

from preza.domain.radar import NewsIn


class SourceUnavailableError(Exception):
    """Network, quota or auth failure; the ingest run records it and moves on."""


class NewsSource(Protocol):
    name: str

    async def fetch(self, since: datetime) -> list[NewsIn]: ...
