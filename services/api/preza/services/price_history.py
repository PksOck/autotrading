"""Archive coherent history and read its two endpoints without mixing price versions."""

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from preza.data.contract import SplitHistory
from preza.domain.history import DEMO_SPLIT_BASIS, IBKR_SPLIT_BASIS, capture_payload
from preza.domain.portfolio_daily import DailyHolding, YearStartPrice, year_to_date_holdings
from preza.models import Instrument, Position, PriceHistoryCapture
from preza.services.market_context import identity_status


def identity_key(instrument: Instrument) -> dict[str, str | int | None]:
    return {
        "symbol": instrument.symbol,
        "currency": instrument.currency,
        "exchange": instrument.exchange,
        "con_id": instrument.ib_con_id,
        "kind": instrument.kind,
    }


async def store_capture(
    session: AsyncSession,
    instrument: Instrument,
    source: str,
    history: SplitHistory,
    *,
    now: datetime | None = None,
    allow_demo: bool = False,
) -> PriceHistoryCapture:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    trusted = source == "ibkr" and history.price_basis == IBKR_SPLIT_BASIS
    demo = (
        allow_demo
        and instrument.source in {"demo", "universe"}
        and source == "demo"
        and history.price_basis == DEMO_SPLIT_BASIS
    )
    if not (trusted or demo) or identity_status(instrument) != "resolved":
        raise ValueError("unverified_history_source")
    if (
        instrument.kind not in {"stock", "etf"}
        or (trusted and (instrument.ib_con_id is None or instrument.ib_con_id <= 0))
        or history.currency != instrument.currency
        or history.con_id <= 0
        or (instrument.ib_con_id is not None and history.con_id != instrument.ib_con_id)
    ):
        raise ValueError("history_identity_mismatch")
    payload = capture_payload(history.bars, now.year, now)
    identity = identity_key(instrument)
    evidence = {
        "identity": identity,
        "source": source,
        "basis": history.price_basis,
        "resolved_con_id": history.con_id,
        "year": now.year,
        "prices": payload.content_hash,
    }
    fingerprint = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
    await session.execute(
        text("SELECT pg_advisory_xact_lock(73160622, :instrument_id)"),
        {"instrument_id": instrument.id},
    )
    latest = await session.scalar(
        select(PriceHistoryCapture)
        .where(
            PriceHistoryCapture.instrument_id == instrument.id, PriceHistoryCapture.year == now.year
        )
        .order_by(PriceHistoryCapture.fetched_at.desc(), PriceHistoryCapture.id.desc())
        .limit(1)
    )
    if latest is not None and latest.fingerprint == fingerprint:
        return latest
    row = PriceHistoryCapture(
        instrument_id=instrument.id,
        year=now.year,
        currency=history.currency,
        resolved_con_id=history.con_id,
        identity=identity,
        source=source,
        price_basis=history.price_basis,
        first_day=payload.first_day,
        last_day=payload.last_day,
        bars=payload.bars,
        fingerprint=fingerprint,
        fetched_at=now,
    )
    session.add(row)
    await session.flush()
    return row


async def latest_captures(
    session: AsyncSession, ids: list[int], year: int
) -> dict[int, PriceHistoryCapture]:
    ranked = (
        select(
            PriceHistoryCapture.id,
            func.row_number()
            .over(
                partition_by=PriceHistoryCapture.instrument_id,
                order_by=(PriceHistoryCapture.fetched_at.desc(), PriceHistoryCapture.id.desc()),
            )
            .label("rn"),
        )
        .where(PriceHistoryCapture.instrument_id.in_(ids), PriceHistoryCapture.year == year)
        .subquery()
    )
    return {
        row.instrument_id: row
        for row in await session.scalars(
            select(PriceHistoryCapture).where(
                PriceHistoryCapture.id.in_(select(ranked.c.id).where(ranked.c.rn == 1))
            )
        )
    }


async def portfolio_ytd_holdings(
    session: AsyncSession,
    positions: list[Position],
    holdings: list[DailyHolding],
    *,
    now: datetime | None = None,
) -> list[DailyHolding]:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    captures = await latest_captures(session, [p.instrument_id for p in positions], now.year)
    result = []
    for position, holding in zip(positions, holdings, strict=True):
        row = captures.get(position.instrument_id)
        if row is None:
            result.append(replace(holding, baseline_reason="missing_year_history"))
            continue
        verified = (row.source == "ibkr" and row.price_basis == IBKR_SPLIT_BASIS) or (
            row.source == "demo"
            and position.source == "demo"
            and row.price_basis == DEMO_SPLIT_BASIS
        )
        if (
            not verified
            or row.identity != identity_key(position.instrument)
            or row.currency != holding.currency
            or row.fetched_at > now
            or row.last_day >= now.date()
        ):
            result.append(replace(holding, baseline_reason="unverified_price_basis"))
            continue
        try:
            first = next(b for b in row.bars if b["day"] == row.first_day.isoformat())
            last = next(b for b in row.bars if b["day"] == row.last_day.isoformat())
            captured = replace(
                holding,
                close=Decimal(last["close"]),
                day=row.last_day,
                source=row.source,
                stale=row.last_day < now.date() - timedelta(days=4),
                capture_id=str(row.id),
                captured_at=row.fetched_at,
                adjustment_basis=row.price_basis,
            )
            pairs = year_to_date_holdings(
                [
                    (
                        captured,
                        YearStartPrice(row.first_day, Decimal(first["close"]), row.source, True),
                    )
                ],
                now.year,
            )
            result.extend(pairs)
        except (KeyError, StopIteration, ValueError, InvalidOperation):
            result.append(replace(holding, baseline_reason="invalid_price"))
    return result
