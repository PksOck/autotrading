"""Read stored market facts in bounded queries; rendering never refreshes providers."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, TypedDict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.metadata import DataMeta, MetricValue
from preza.models import Bar, EtfProfile, Fundamentals, Instrument

METRICS = {
    "pe": "multiple",
    "forward_pe": "multiple",
    "ev_ebit": "multiple",
    "fcf_yield": "percent",
    "roe_pct": "percent",
    "gross_margin_pct": "percent",
    "net_margin_pct": "percent",
    "revenue_growth_pct": "percent",
    "debt_to_equity": "ratio",
    "dividend_yield_pct": "percent",
    "payout_ratio_pct": "percent",
    "dividend_per_share": "currency/share",
}


class MarketContext(TypedDict):
    metrics: dict[str, MetricValue]
    price_meta: DataMeta
    change_pct: Decimal | None
    latest_close: str | None


def identity_status(instrument: Instrument) -> str:
    return (
        "resolved"
        if instrument.kind != "unknown" and instrument.currency and instrument.exchange
        else "unresolved"
    )


async def market_context(session: AsyncSession, ids: list[int]) -> dict[int, MarketContext]:
    if not ids:
        return {}
    ranked = (
        select(
            Bar,
            func.row_number()
            .over(partition_by=Bar.instrument_id, order_by=Bar.day.desc())
            .label("rn"),
        )
        .where(Bar.instrument_id.in_(ids), Bar.interval == "1d")
        .subquery()
    )
    bars = (
        (
            await session.execute(
                select(ranked)
                .where(ranked.c.rn <= 2)
                .order_by(ranked.c.instrument_id, ranked.c.day.desc())
            )
        )
        .mappings()
        .all()
    )
    by_id: dict[int, list[dict[str, Any]]] = {}
    for bar in bars:
        by_id.setdefault(bar["instrument_id"], []).append(dict(bar))
    funds = {
        f.instrument_id: f
        for f in await session.scalars(
            select(Fundamentals).where(Fundamentals.instrument_id.in_(ids))
        )
    }
    profiles = {
        e.instrument_id: e
        for e in await session.scalars(select(EtfProfile).where(EtfProfile.instrument_id.in_(ids)))
    }
    instruments = list(await session.scalars(select(Instrument).where(Instrument.id.in_(ids))))
    out: dict[int, MarketContext] = {}
    now = datetime.now(UTC)
    for instrument in instruments:
        recent = by_id.get(instrument.id, [])
        latest = recent[0] if recent else None
        price_meta = DataMeta(
            source=str(latest["source"]) if latest else None,
            market_date=latest["day"] if latest else None,
            fetched_at=latest["fetched_at"] if latest else None,
            availability="available" if latest else "missing",
            reason_code=None if latest else "no_observation",
            stale=bool(latest and latest["day"] < now.date() - timedelta(days=4)),
            basis="daily_close",
        )
        metrics: dict[str, MetricValue] = {}
        fund = funds.get(instrument.id)
        for key, unit in METRICS.items():
            raw = fund.metrics.get(key) if fund else None
            value: str | None = None
            try:
                if raw is not None and not isinstance(raw, bool) and Decimal(str(raw)).is_finite():
                    value = str(raw)
            except InvalidOperation:
                pass
            meta = (fund.metrics_meta or {}).get(key, {}) if fund else {}
            metrics[key] = MetricValue(
                value=value,
                unit=unit,
                meta=DataMeta(
                    source=fund.source if fund else None,
                    market_date=fund.as_of if fund and meta.get("period_end") else None,
                    fetched_at=fund.fetched_at if fund else None,
                    availability="not_applicable"
                    if instrument.kind == "etf"
                    else "available"
                    if value is not None and meta
                    else "partial"
                    if value is not None
                    else "missing",
                    reason_code="unsupported_instrument"
                    if instrument.kind == "etf"
                    else "identity_unresolved"
                    if identity_status(instrument) == "unresolved"
                    else "basis_unverified"
                    if value is not None and not meta
                    else None
                    if value is not None
                    else "no_observation",
                    stale=bool(fund and fund.fetched_at < now - timedelta(days=8)),
                    basis=meta.get("basis"),
                    source_field=meta.get("source_field"),
                ),
            )
        profile = profiles.get(instrument.id)
        for key in ("ter", "index_name", "distribution"):
            raw = getattr(profile, key, None) if profile else None
            metrics[key] = MetricValue(
                value=str(raw) if raw is not None else None,
                unit="fraction" if key == "ter" else "text",
                meta=DataMeta(
                    source=(profile.ter_source if key == "ter" else profile.source)
                    if profile
                    else None,
                    market_date=(profile.ter_as_of if key == "ter" else profile.as_of)
                    if profile
                    else None,
                    fetched_at=profile.fetched_at if profile else None,
                    availability="not_applicable"
                    if instrument.kind == "stock"
                    else "available"
                    if raw is not None
                    else "missing",
                    reason_code="unsupported_instrument"
                    if instrument.kind == "stock"
                    else None
                    if raw is not None
                    else "no_observation",
                ),
            )
        change = None
        if len(recent) == 2 and recent[1]["close"]:
            change = (recent[0]["close"] / recent[1]["close"] - 1) * 100
        out[instrument.id] = {
            "metrics": metrics,
            "price_meta": price_meta,
            "change_pct": change,
            "latest_close": str(latest["close"]) if latest else None,
        }
    return out
