"""Instrument lookup and creation."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.market import InstrumentKind
from preza.models import Instrument

ETF_EXCHANGES = {"LSEETF", "IBIS2"}


async def find_by_symbol(session: AsyncSession, symbol: str) -> Instrument | None:
    """Prefers the user's tradable listing when a symbol exists on several exchanges."""
    rows = await session.scalars(
        select(Instrument)
        .where(Instrument.symbol == symbol.upper())
        .order_by(
            Instrument.tradable_for_user.desc(), Instrument.ib_con_id.is_(None), Instrument.id
        )
    )
    return rows.first()


async def search(session: AsyncSession, query: str, limit: int = 20) -> list[Instrument]:
    q = query.strip().upper()
    if not q:
        return []
    rows = await session.scalars(
        select(Instrument)
        .where(or_(Instrument.symbol.startswith(q), Instrument.name.ilike(f"%{query.strip()}%")))
        .order_by((Instrument.symbol == q).desc(), Instrument.symbol)
        .limit(limit)
    )
    return list(rows)


async def get_or_create(
    session: AsyncSession,
    *,
    symbol: str,
    source: str,
    exchange: str | None = None,
    con_id: int | None = None,
    name: str | None = None,
    kind: InstrumentKind = InstrumentKind.UNKNOWN,
    currency: str | None = None,
    isin: str | None = None,
) -> Instrument:
    """Matches by IBKR conId, then symbol+exchange. Fills gaps, never overwrites known data."""
    instrument: Instrument | None = None
    if con_id is not None:
        instrument = await session.scalar(select(Instrument).where(Instrument.ib_con_id == con_id))
    if instrument is None:
        instrument = await session.scalar(
            select(Instrument).where(
                Instrument.symbol == symbol.upper(),
                Instrument.exchange.is_(None)
                if exchange is None
                else Instrument.exchange == exchange,
            )
        )
    if instrument is None:
        instrument = Instrument(
            symbol=symbol.upper(), exchange=exchange, source=source, kind=kind.value
        )
        session.add(instrument)

    instrument.ib_con_id = instrument.ib_con_id or con_id
    instrument.name = instrument.name or name
    instrument.currency = instrument.currency or currency
    instrument.isin = instrument.isin or isin
    if instrument.kind == InstrumentKind.UNKNOWN.value and kind != InstrumentKind.UNKNOWN:
        instrument.kind = kind.value
    if isin and isin[:2] in ("IE", "LU") and instrument.kind == InstrumentKind.ETF.value:
        instrument.ucits = True
        instrument.domicile = isin[:2]
    await session.flush()
    return instrument
