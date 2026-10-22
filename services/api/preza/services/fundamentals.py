"""Refresh stored fundamentals and rebuild valuation bands from them (BL-061)."""

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.valuation import ValuationBand, summary_score, valuation_bands
from preza.fundamentals.finnhub import FinnhubFundamentals
from preza.models import Fundamentals, Instrument


async def refresh_fundamentals(
    session: AsyncSession, instrument: Instrument, client: FinnhubFundamentals
) -> Fundamentals | None:
    """Fetch and upsert the row; ETFs have no company fundamentals and are skipped.

    Raises FundamentalsUnavailableError from the client; the caller decides how to record it.
    """
    if instrument.kind == "etf":
        return None
    snap = await client.fetch(instrument.symbol)
    history = {
        metric: [[d.isoformat(), v] for d, v in points] for metric, points in snap.history.items()
    }
    row = await session.get(Fundamentals, instrument.id)
    if row is None:
        row = Fundamentals(instrument_id=instrument.id)
        session.add(row)
    row.as_of = snap.as_of
    row.metrics = dict(snap.metrics)
    row.history = history
    row.source = snap.source
    row.fetched_at = datetime.now(UTC)
    await session.flush()
    return row


def bands_for(fund: Fundamentals) -> dict[str, ValuationBand]:
    history: dict[str, list[tuple[date, float]]] = {}
    for metric, points in (fund.history or {}).items():
        history[metric] = [(date.fromisoformat(str(d)), float(v)) for d, v in points]
    current = {k: (float(v) if v is not None else None) for k, v in (fund.metrics or {}).items()}
    return valuation_bands(current, history, fund.as_of)


def bands_json(bands: dict[str, ValuationBand]) -> dict[str, Any]:
    out: dict[str, Any] = {
        metric: {
            "current": b.current,
            "median": b.median,
            "p20": b.p20,
            "p80": b.p80,
            "percentile": b.percentile,
            "cheap": b.cheap,
            "n": b.n,
            "as_of": b.as_of.isoformat(),
        }
        for metric, b in bands.items()
    }
    out["summary"] = summary_score(bands)
    return out
