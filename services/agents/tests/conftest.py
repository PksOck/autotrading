from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from preza_agents.deep_research import vendor_local
from preza_agents.deep_research.snapshot import BarRow, DataSnapshot, NewsRow

AS_OF = date(2026, 10, 20)


def make_snapshot(symbol: str = "ASML", days: int = 320) -> DataSnapshot:
    bars = []
    # Walk back from the run date so the last bar is AS_OF itself.
    first = AS_OF
    count = 0
    while count < days:
        if first.weekday() < 5:
            count += 1
        first -= timedelta(days=1)
    day = first + timedelta(days=1)
    i = 0
    while day <= AS_OF:
        if day.weekday() < 5:
            close = 700 + 40 * math.sin(i / 17) + i * 0.3
            bars.append(
                BarRow(
                    day=day,
                    open=Decimal(f"{close - 2:.2f}"),
                    high=Decimal(f"{close + 5:.2f}"),
                    low=Decimal(f"{close - 6:.2f}"),
                    close=Decimal(f"{close:.2f}"),
                    volume=1_000_000 + i,
                )
            )
            i += 1
        day += timedelta(days=1)
    # A bar after the run date must never be served.
    bars.append(
        BarRow(
            day=AS_OF + timedelta(days=1),
            open=Decimal(1),
            high=Decimal(1),
            low=Decimal(1),
            close=Decimal("1.00"),
            volume=1,
        )
    )
    ts = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
    news = [
        NewsRow(
            published_at=ts,
            title="ASML wins a large order",
            source="press_release",
            url="https://example.com/a",
            kind="press_release",
            symbols=[symbol],
        ),
        NewsRow(
            published_at=ts - timedelta(days=1),
            title="ASML may be acquired",
            source="reddit",
            url="https://example.com/b",
            kind="social",
            is_rumor=True,
            symbols=[symbol],
        ),
        NewsRow(
            published_at=ts - timedelta(days=2),
            title="Form 4: CFO buys shares",
            source="sec_edgar",
            url="https://example.com/c",
            kind="filing",
            filing_form="4",
            symbols=[symbol],
        ),
    ]
    return DataSnapshot(
        symbol=symbol,
        name="ASML Holding N.V.",
        kind="stock",
        exchange="NASDAQ",
        currency="USD",
        as_of=AS_OF,
        bars=bars,
        bars_source="ibkr",
        fundamentals={"peTTM": 31.2, "marketCapitalization": 290000.0},
        fundamentals_source="finnhub",
        fundamentals_as_of=date(2026, 10, 19),
        news=news,
        global_news=[
            NewsRow(
                published_at=ts,
                title="Fed holds rates",
                source="rss",
                url="https://example.com/d",
                kind="news",
            )
        ],
    )


@pytest.fixture
def snapshot() -> DataSnapshot:
    vendor_local.install()
    return make_snapshot()
