"""Five fixed data snapshots for agent regression tests (BL-086).

Synthetic but deterministic: each one stresses a different path (trend, rumor rule,
missing fundamentals, short history, a fund). Real-market snapshots can be added the
same way once the live data checks (BL-059, BL-066, BL-091) are done.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from preza_agents.deep_research.snapshot import BarRow, DataSnapshot, NewsRow

AS_OF = date(2026, 10, 20)
TS = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)


def _days(count: int) -> list[date]:
    days: list[date] = []
    day = AS_OF
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    return days[::-1]


def bars(count: int, start: float, drift: float, wave: float, atr: float) -> list[BarRow]:
    rows = []
    for i, day in enumerate(_days(count)):
        close = start + drift * i + wave * math.sin(i / 13)
        rows.append(
            BarRow(
                day=day,
                open=Decimal(f"{close - atr / 4:.2f}"),
                high=Decimal(f"{close + atr / 2:.2f}"),
                low=Decimal(f"{close - atr / 2:.2f}"),
                close=Decimal(f"{close:.2f}"),
                volume=2_000_000 + 1000 * (i % 17),
            )
        )
    return rows


def news(
    symbol: str, title: str, kind: str, days_ago: int, rumor: bool = False, form: str | None = None
) -> NewsRow:
    return NewsRow(
        published_at=TS - timedelta(days=days_ago),
        title=title,
        source="sec_edgar" if kind == "filing" else ("reddit" if rumor else "press_release"),
        url=f"https://example.com/{symbol.lower()}/{days_ago}",
        kind=kind,
        is_rumor=rumor,
        filing_form=form,
        symbols=[symbol],
    )


def history(values: list[float]) -> list[tuple[date, float]]:
    return [(AS_OF - timedelta(days=91 * (i + 1)), v) for i, v in enumerate(values)]


MACRO = [
    NewsRow(
        published_at=TS,
        title="Fed holds rates steady",
        source="rss",
        url="https://example.com/macro",
        kind="news",
    )
]


def uptrend_cheap() -> DataSnapshot:
    """Rising stock, cheaper than its own history, official news only."""
    return DataSnapshot(
        symbol="ACME",
        name="Acme Semiconductor",
        exchange="NASDAQ",
        currency="USD",
        as_of=AS_OF,
        bars=bars(320, 100, 0.25, 4, 2.0),
        bars_source="ibkr",
        fundamentals={
            "pe": 18.0,
            "ev_ebit": 14.0,
            "fcf_yield": 5.5,
            "roe_pct": 24.0,
            "net_margin_pct": 18.0,
            "revenue_growth_pct": 9.0,
            "debt_to_equity": 0.4,
        },
        fundamentals_source="finnhub",
        fundamentals_as_of=AS_OF - timedelta(days=1),
        fundamentals_history={
            "pe": history([24, 26, 22, 25, 27, 23, 21, 24, 26, 25, 22, 23]),
            "ev_ebit": history([18, 19, 17, 20, 21, 18, 16, 19, 20, 18, 17, 19]),
            "fcf_yield": history([3.5, 3.8, 4.0, 3.2, 3.9, 4.1, 3.6, 3.3, 3.7, 4.2, 3.4, 3.8]),
        },
        news=[
            news("ACME", "Acme raises full-year guidance", "press_release", 1),
            news("ACME", "Form 4: director buys shares", "filing", 3, form="4"),
        ],
        global_news=MACRO,
    )


def downtrend_expensive() -> DataSnapshot:
    """Falling, volatile stock, dearer than its own history."""
    return DataSnapshot(
        symbol="BOLT",
        name="Bolt Motors",
        exchange="NYSE",
        currency="USD",
        as_of=AS_OF,
        bars=bars(320, 220, -0.35, 6, 9.0),
        bars_source="ibkr",
        fundamentals={
            "pe": 61.0,
            "ev_ebit": 48.0,
            "fcf_yield": 0.8,
            "roe_pct": 4.0,
            "net_margin_pct": 2.0,
            "revenue_growth_pct": -6.0,
            "debt_to_equity": 2.6,
        },
        fundamentals_source="finnhub",
        fundamentals_as_of=AS_OF - timedelta(days=1),
        fundamentals_history={
            "pe": history([35, 40, 38, 42, 37, 39, 41, 36, 44, 40]),
            "ev_ebit": history([28, 30, 29, 31, 27, 33, 30, 29, 32, 31]),
            "fcf_yield": history([2.0, 1.8, 2.2, 1.9, 2.1, 2.4, 1.7, 2.0, 2.3, 1.9]),
        },
        news=[news("BOLT", "Bolt recalls 40,000 vehicles", "press_release", 2)],
        global_news=MACRO,
    )


def rumor_only() -> DataSnapshot:
    """The only company news is an unconfirmed takeover rumor (AGENTS.md rule 4)."""
    snap = uptrend_cheap()
    return snap.model_copy(
        update={
            "symbol": "RUMR",
            "name": "Rumor Robotics",
            "news": [news("RUMR", "Rumor Robotics may be bought by a rival", "social", 1, True)],
        }
    )


def short_history() -> DataSnapshot:
    """A recent listing: 120 sessions, no fundamentals yet."""
    return DataSnapshot(
        symbol="NEWC",
        name="Newco Software",
        exchange="NASDAQ",
        currency="USD",
        as_of=AS_OF,
        bars=bars(120, 40, 0.05, 2, 1.5),
        bars_source="ibkr",
        news=[news("NEWC", "Newco reports first quarter as a public company", "press_release", 5)],
        global_news=MACRO,
    )


def etf_fund() -> DataSnapshot:
    """A UCITS fund: bars only, the ETF engine reads its profile separately."""
    return DataSnapshot(
        symbol="SEMI",
        name="iShares MSCI Global Semiconductors UCITS ETF (Acc)",
        kind="etf",
        exchange="LSEETF",
        currency="USD",
        as_of=AS_OF,
        bars=bars(320, 8, 0.01, 0.4, 0.15),
        bars_source="ibkr",
        global_news=MACRO,
    )


SCENARIOS: dict[str, Callable[[], DataSnapshot]] = {
    "uptrend_cheap": uptrend_cheap,
    "downtrend_expensive": downtrend_expensive,
    "rumor_only": rumor_only,
    "short_history": short_history,
    "etf_fund": etf_fund,
}
