"""Daily bars: read from the database, top up from providers when stale (BL-024)."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from preza.data.contract import InstrumentRef, ProviderError
from preza.data.router import BarsRouter
from preza.domain.market import BarIn
from preza.models import Bar, Instrument, SyncRun

log = logging.getLogger(__name__)


def last_trading_day(today: date) -> date:
    """Most recent weekday on or before `today` (holidays are tolerated as one stale day)."""
    day = today
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


@dataclass
class BarsResult:
    bars: list[Bar]
    source: str | None
    fetched_at: datetime | None
    stale: bool


async def upsert_bars(
    session: AsyncSession, instrument_id: int, bars: Sequence[BarIn], source: str
) -> int:
    if not bars:
        return 0
    now = datetime.now(UTC)
    rows = [
        {
            "instrument_id": instrument_id,
            "interval": "1d",
            "day": b.day,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
            "source": source,
            "fetched_at": now,
        }
        for b in bars
    ]
    stmt = insert(Bar).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["instrument_id", "interval", "day"],
        set_={
            k: stmt.excluded[k]
            for k in ("open", "high", "low", "close", "volume", "source", "fetched_at")
        },
    )
    await session.execute(stmt)
    return len(rows)


class BarsService:
    def __init__(self, router: BarsRouter, lookback_days: int = 800):
        self.router = router
        self.lookback_days = lookback_days

    async def refresh_year_history(
        self, session: AsyncSession, instrument: Instrument, today: date | None = None
    ) -> bool:
        from preza.services.market_context import identity_status
        from preza.services.price_history import identity_key, latest_captures, store_capture

        today = today or datetime.now(UTC).date()
        fetch = getattr(self.router, "split_history", None)
        if (
            fetch is None
            or instrument.kind not in {"stock", "etf"}
            or identity_status(instrument) != "resolved"
            or instrument.ib_con_id is None
            or instrument.ib_con_id <= 0
        ):
            return False
        latest = (await latest_captures(session, [instrument.id], today.year)).get(instrument.id)
        if (
            latest is not None
            and latest.identity == identity_key(instrument)
            and latest.source == "ibkr"
            and latest.fetched_at <= datetime.now(UTC)
            and latest.last_day >= last_trading_day(today - timedelta(days=1))
        ):
            return True
        run = SyncRun(kind="ytd_history", status="running", detail=instrument.symbol)
        session.add(run)
        try:
            source, history = await fetch(
                InstrumentRef(
                    instrument.symbol,
                    instrument.exchange,
                    instrument.currency,
                    instrument.ib_con_id,
                ),
                date(today.year, 1, 1) - timedelta(days=7),
            )
            row = await store_capture(session, instrument, source, history)
            run.status, run.detail = "ok", f"{instrument.symbol}: {row.id} {row.price_basis}"
            return True
        except (ProviderError, ValueError, TimeoutError, OSError) as exc:
            run.status, run.detail = "failed", f"{instrument.symbol}: {type(exc).__name__}"
            return False
        finally:
            run.finished_at = datetime.now(UTC)

    async def refresh(
        self, session: AsyncSession, instrument: Instrument, today: date | None = None
    ) -> bool:
        """Fetches missing bars. Returns False (and logs a SyncRun) when every provider failed."""
        today = today or date.today()
        latest = await session.scalar(
            select(func.max(Bar.day)).where(Bar.instrument_id == instrument.id)
        )
        if latest is not None and latest >= last_trading_day(today):
            return True
        start = (
            (latest + timedelta(days=1)) if latest else today - timedelta(days=self.lookback_days)
        )
        ref = InstrumentRef(
            instrument.symbol, instrument.exchange, instrument.currency, instrument.ib_con_id
        )
        run = SyncRun(kind="bars", status="running", detail=instrument.symbol)
        session.add(run)
        try:
            routed = await self.router.daily_bars(ref, start)
        except ProviderError as exc:
            run.status, run.finished_at, run.detail = (
                "failed",
                datetime.now(UTC),
                f"{instrument.symbol}: {exc}",
            )
            log.warning("bars refresh failed for %s: %s", instrument.symbol, exc)
            return False
        count = await upsert_bars(session, instrument.id, routed.bars, routed.provider)
        run.status, run.finished_at = "ok", datetime.now(UTC)
        run.detail = f"{instrument.symbol}: {count} bars from {routed.provider}"
        return True

    async def read(self, session: AsyncSession, instrument: Instrument, since: date) -> BarsResult:
        bars = list(
            await session.scalars(
                select(Bar)
                .where(Bar.instrument_id == instrument.id, Bar.day >= since)
                .order_by(Bar.day)
            )
        )
        if not bars:
            return BarsResult(bars=[], source=None, fetched_at=None, stale=True)
        last = bars[-1]
        stale = last.day < last_trading_day(date.today()) - timedelta(days=1)
        return BarsResult(bars=bars, source=last.source, fetched_at=last.fetched_at, stale=stale)


def change_pct(bars: list[Bar]) -> Decimal | None:
    if len(bars) < 2 or not bars[-2].close:
        return None
    return (bars[-1].close / bars[-2].close - 1) * 100
