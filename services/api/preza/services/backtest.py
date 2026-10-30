"""Deterministic read-only event study; no providers, orders or model calls."""

from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Literal, cast

from sqlalchemy import (
    Date,
    Integer,
    Numeric,
    String,
    column,
    func,
    literal,
    select,
    true,
    union_all,
    values,
)
from sqlalchemy import cast as sql_cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from preza.domain.backtest import BacktestOut, BacktestRequest, BacktestRow, EventStudyResult
from preza.models import AnalysisRun, Bar, Instrument, Signal


def evaluate_record(
    *, available_at: datetime, direction: str, bars: list[Bar], horizon: int, cost_bps: Decimal
) -> EventStudyResult:
    if direction not in ("up", "down"):
        return EventStudyResult(skip_reason="neutral_or_unknown_direction")
    available_day = available_at.astimezone(UTC).date()
    eligible = sorted((bar for bar in bars if bar.day > available_day), key=lambda bar: bar.day)
    if not eligible:
        return EventStudyResult(skip_reason="no_entry_bar")
    entry = eligible[0]
    result = EventStudyResult(
        entry_date=entry.day, entry_price=entry.close, entry_source=entry.source
    )
    if len(eligible) <= horizon:
        result.skip_reason = "insufficient_future_sessions"
        return result
    exit_bar = eligible[horizon]
    result.exit_date = exit_bar.day
    result.exit_price = exit_bar.close
    result.exit_source = exit_bar.source
    if entry.close <= 0 or exit_bar.close <= 0:
        result.skip_reason = "invalid_price"
        return result
    ratio = exit_bar.close / entry.close
    gross = (ratio - 1) * (1 if direction == "up" else -1) * 100
    # Fees on each side's traded notional, expressed relative to the entry notional.
    fees_pct = cost_bps / 100 * (1 + ratio)
    result.gross_return_pct = gross
    result.net_return_pct = gross - fees_pct
    return result


def opinion_direction(rating: str | None) -> str:
    return {"buy": "up", "overweight": "up", "sell": "down", "underweight": "down"}.get(
        (rating or "").strip().lower(), "neutral"
    )


async def run_backtest(session: AsyncSession, request: BacktestRequest) -> BacktestOut:
    now = datetime.now(UTC)
    signal_query = select(
        sql_cast(Signal.id, String).label("id"),
        literal("signal").label("source"),
        Signal.source.label("origin"),
        Signal.instrument_id.label("instrument_id"),
        Signal.created_at.label("available_at"),
        Signal.direction.label("direction"),
        Signal.strength.label("strength"),
        Signal.status.label("record_status"),
    ).where(Signal.strength >= request.min_strength)
    if request.signal_status != "all":
        signal_query = signal_query.where(Signal.status == request.signal_status)
    analysis_query = select(
        sql_cast(AnalysisRun.id, String).label("id"),
        literal("analysis").label("source"),
        AnalysisRun.engine.label("origin"),
        AnalysisRun.instrument_id.label("instrument_id"),
        AnalysisRun.finished_at.label("available_at"),
        AnalysisRun.rating.label("direction"),
        sql_cast(literal(None), Numeric).label("strength"),
        AnalysisRun.status.label("record_status"),
    ).where(AnalysisRun.status == "done", AnalysisRun.finished_at.is_not(None))
    queries = {"signal": signal_query, "analysis": analysis_query}
    records = (
        union_all(signal_query, analysis_query).subquery()
        if request.source == "all"
        else queries[request.source].subquery()
    )
    filters = [records.c.available_at <= now]
    if request.available_from:
        filters.append(
            records.c.available_at >= datetime.combine(request.available_from, time(), UTC)
        )
    if request.available_to:
        filters.append(
            records.c.available_at
            < datetime.combine(request.available_to + timedelta(days=1), time(), UTC)
        )
    total = await session.scalar(select(func.count()).select_from(records).where(*filters)) or 0
    candidates = (
        (
            await session.execute(
                select(records, Instrument.symbol, Instrument.currency)
                .join(Instrument, Instrument.id == records.c.instrument_id)
                .where(*filters)
                .order_by(records.c.available_at, records.c.source, records.c.id)
                .limit(request.limit)
            )
        )
        .mappings()
        .all()
    )
    grouped: dict[tuple[str, str], list[Bar]] = defaultdict(list)
    if candidates:
        # One bounded indexed lookup per candidate inside one SQL request. A long-lived
        # instrument never loads its entire history; at most limit * (horizon + 1) rows.
        history_inputs = values(
            column("record_id", String),
            column("record_source", String),
            column("instrument_id", Integer),
            column("available_day", Date),
            name="history_inputs",
        ).data(
            [
                (
                    row["id"],
                    row["source"],
                    row["instrument_id"],
                    row["available_at"].astimezone(UTC).date(),
                )
                for row in candidates
            ]
        )
        next_bars = (
            select(Bar)
            .where(
                Bar.instrument_id == history_inputs.c.instrument_id,
                Bar.interval == "1d",
                Bar.day > history_inputs.c.available_day,
                Bar.day < now.date(),
            )
            .order_by(Bar.day)
            .limit(request.horizon_sessions + 1)
            .correlate(history_inputs)
            .lateral("next_bars")
        )
        bounded_bar = aliased(Bar, next_bars)
        for record_id, record_source, bar in await session.execute(
            select(
                history_inputs.c.record_id, history_inputs.c.record_source, bounded_bar
            ).select_from(history_inputs.join(next_bars, true()))
        ):
            grouped[(record_source, record_id)].append(bar)
    rows = []
    for record in candidates:
        direction = (
            opinion_direction(record["direction"])
            if record["source"] == "analysis"
            else record["direction"]
        )
        result = evaluate_record(
            available_at=record["available_at"],
            direction=direction,
            bars=grouped[(record["source"], record["id"])],
            horizon=request.horizon_sessions,
            cost_bps=request.cost_bps,
        )
        rows.append(
            BacktestRow(
                id=record["id"],
                source=cast(Literal["signal", "analysis"], record["source"]),
                origin=record["origin"],
                symbol=record["symbol"],
                currency=record["currency"],
                available_at=record["available_at"],
                direction=direction,
                strength=record["strength"],
                record_status=record["record_status"],
                **result.model_dump(),
            )
        )
    completed = [row for row in rows if row.net_return_pct is not None]
    count = len(completed)
    return BacktestOut(
        as_of=now,
        parameters=request,
        total_matching=total,
        evaluated=len(rows),
        truncated=total > len(rows),
        completed=count,
        skipped=len(rows) - count,
        mean_gross_return_pct=sum(
            (row.gross_return_pct for row in completed if row.gross_return_pct is not None),
            Decimal(0),
        )
        / count
        if count
        else None,
        mean_net_return_pct=sum(
            (row.net_return_pct for row in completed if row.net_return_pct is not None), Decimal(0)
        )
        / count
        if count
        else None,
        positive_share=Decimal(
            sum(row.net_return_pct > 0 for row in completed if row.net_return_pct is not None)
        )
        / count
        if count
        else None,
        rows=rows,
    )
