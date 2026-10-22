"""Nightly signal outcome computation and aggregate stats (BL-065)."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.outcome import HORIZONS, DayBar, OutcomeStat, compute_outcome
from preza.models import Bar, Signal, SignalOutcome
from preza.services.instruments import find_by_symbol

_Q = Decimal("0.0001")


async def _load_bars(session: AsyncSession, instrument_id: int, since: Any) -> list[DayBar]:
    rows = await session.execute(
        select(Bar.day, Bar.high, Bar.low, Bar.close)
        .where(Bar.instrument_id == instrument_id, Bar.interval == "1d", Bar.day >= since)
        .order_by(Bar.day)
    )
    return [DayBar(day=r.day, high=r.high, low=r.low, close=r.close) for r in rows]


async def compute_outcomes(
    session: AsyncSession, benchmark_symbol: str = "SPY", now: datetime | None = None
) -> int:
    """Inserts missing SignalOutcome rows whose data is available; returns rows inserted."""
    now = now or datetime.now(UTC)
    done_rows = await session.execute(select(SignalOutcome.signal_id, SignalOutcome.horizon_days))
    done: dict[Any, set[int]] = defaultdict(set)
    for signal_id, horizon in done_rows:
        done[signal_id].add(horizon)

    signals = (await session.scalars(select(Signal).order_by(Signal.created_at))).all()
    by_instrument: dict[int, list[tuple[Signal, list[int]]]] = defaultdict(list)
    for sig in signals:
        missing = [h for h in HORIZONS if h not in done.get(sig.id, set())]
        if not missing:
            continue
        by_instrument[sig.instrument_id].append((sig, missing))
    if not by_instrument:
        return 0

    bench_inst = await find_by_symbol(session, benchmark_symbol)
    bench_name = bench_inst.symbol if bench_inst else None
    all_days = [
        s.created_at.astimezone(UTC).date() for items in by_instrument.values() for s, _ in items
    ]
    bench_bars: list[DayBar] | None = None
    if bench_inst:
        bench_bars = await _load_bars(session, bench_inst.id, min(all_days) - timedelta(days=10))

    inserted = 0
    for instrument_id, items in by_instrument.items():
        first_day = min(s.created_at.astimezone(UTC).date() for s, _ in items)
        bars = await _load_bars(session, instrument_id, first_day)
        if not bars:
            continue
        for sig, missing in items:
            signal_day = sig.created_at.astimezone(UTC).date()
            for horizon in missing:
                out = compute_outcome(bars, signal_day, horizon, sig.direction, bench_bars)
                if out is None:
                    continue
                session.add(
                    SignalOutcome(
                        signal_id=sig.id,
                        horizon_days=horizon,
                        start_day=out.start_day,
                        end_day=out.end_day,
                        start_price=out.start_price,
                        end_price=out.end_price,
                        return_pct=out.return_pct,
                        benchmark=bench_name if out.benchmark_return_pct is not None else None,
                        benchmark_return_pct=out.benchmark_return_pct,
                        alpha_pct=out.alpha_pct,
                        mfe_pct=out.mfe_pct,
                        mae_pct=out.mae_pct,
                        computed_at=now,
                    )
                )
                inserted += 1
    await session.flush()
    return inserted


async def outcome_stats(session: AsyncSession) -> list[dict[str, Any]]:
    """Per (kind, source, horizon): count, hit rate (return > 0), avg return, avg alpha."""
    hit = func.avg(case((SignalOutcome.return_pct > 0, 1), else_=0))
    rows = await session.execute(
        select(
            Signal.kind,
            Signal.source,
            SignalOutcome.horizon_days,
            func.count(),
            hit,
            func.avg(SignalOutcome.return_pct),
            func.avg(SignalOutcome.alpha_pct),
        )
        .join(Signal, Signal.id == SignalOutcome.signal_id)
        .group_by(Signal.kind, Signal.source, SignalOutcome.horizon_days)
        .order_by(Signal.kind, Signal.source, SignalOutcome.horizon_days)
    )
    stats: list[OutcomeStat] = []
    for kind, source, horizon, count, hit_rate, avg_ret, avg_alpha in rows:
        stats.append(
            OutcomeStat(
                kind=kind,
                source=source,
                horizon_days=horizon,
                count=count,
                hit_rate=Decimal(hit_rate).quantize(_Q),
                avg_return_pct=Decimal(avg_ret).quantize(_Q),
                avg_alpha_pct=None if avg_alpha is None else Decimal(avg_alpha).quantize(_Q),
            )
        )
    return [s.model_dump() for s in stats]
