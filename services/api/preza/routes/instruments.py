import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from preza.db import get_session
from preza.deps import get_bars_service
from preza.domain.market import BarOut, BarsOut, InstrumentDetail, InstrumentOut, Provenance
from preza.services import instruments
from preza.services.bars import BarsService, change_pct
from preza.services.watchlist import bars_since

router = APIRouter(prefix="/instruments", tags=["instruments"])
Session = Annotated[AsyncSession, Depends(get_session)]
Bars = Annotated[BarsService, Depends(get_bars_service)]

REFRESH_TIMEOUT_S = 20


@router.get("", response_model=list[InstrumentOut])
async def search(
    session: Session, q: Annotated[str, Query(min_length=1, max_length=40)]
) -> list[InstrumentOut]:
    return [InstrumentOut.model_validate(i) for i in await instruments.search(session, q)]


async def _instrument_or_404(session: AsyncSession, symbol: str):  # type: ignore[no-untyped-def]
    instrument = await instruments.find_by_symbol(session, symbol)
    if instrument is None:
        raise HTTPException(404, detail="instrument_not_found")
    return instrument


@router.get("/{symbol}", response_model=InstrumentDetail)
async def detail(session: Session, bars_service: Bars, symbol: str) -> InstrumentDetail:
    instrument = await _instrument_or_404(session, symbol)
    result = await bars_service.read(session, instrument, bars_since("1m"))
    change = change_pct(result.bars)
    return InstrumentDetail(
        **InstrumentOut.model_validate(instrument).model_dump(),
        last_close=result.bars[-1].close if result.bars else None,
        change_pct=change,
        provenance=Provenance(source=result.source, as_of=result.fetched_at, stale=result.stale)
        if result.source and result.fetched_at
        else None,
    )


@router.get("/{symbol}/bars", response_model=BarsOut)
async def bars(
    session: Session,
    bars_service: Bars,
    symbol: str,
    range: Annotated[str, Query(pattern="^(1m|3m|1y|2y|5y)$")] = "1y",
    refresh: bool = True,
) -> BarsOut:
    instrument = await _instrument_or_404(session, symbol)
    if refresh:
        # Never let a slow provider block the page: serve what is stored after the timeout.
        try:
            await asyncio.wait_for(bars_service.refresh(session, instrument), REFRESH_TIMEOUT_S)
        except TimeoutError:
            pass
    result = await bars_service.read(session, instrument, bars_since(range))
    return BarsOut(
        symbol=instrument.symbol,
        bars=[BarOut.model_validate(b) for b in result.bars],
        provenance=Provenance(source=result.source, as_of=result.fetched_at, stale=result.stale)
        if result.source and result.fetched_at
        else None,
    )
