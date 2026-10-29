import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings, get_settings
from preza.db import get_session
from preza.deps import get_bars_service
from preza.domain.market import (
    BarOut,
    BarsOut,
    IdentityEnrichInput,
    IdentityEnrichOut,
    InstrumentDetail,
    InstrumentOut,
    Provenance,
)
from preza.services import instruments
from preza.services.bars import BarsService, change_pct
from preza.services.identity import IdentityError, enrich_identity
from preza.services.market_context import identity_status, market_context
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
    context = (await market_context(session, [instrument.id]))[instrument.id]
    return InstrumentDetail(
        **InstrumentOut.model_validate(instrument).model_dump(),
        instrument_id=instrument.id,
        identity_source=instrument.source,
        identity_updated_at=instrument.updated_at,
        identity_status=identity_status(instrument),
        metrics=context["metrics"],
        price_meta=context["price_meta"],
        last_close=result.bars[-1].close if result.bars else None,
        change_pct=change,
        provenance=Provenance(source=result.source, as_of=result.fetched_at, stale=result.stale)
        if result.source and result.fetched_at
        else None,
    )


@router.post("/{symbol}/identity/enrich", response_model=IdentityEnrichOut)
async def enrich(
    symbol: str,
    body: IdentityEnrichInput,
    session: Session,
    settings: Annotated[Settings, Depends(get_settings)],
) -> IdentityEnrichOut:
    try:
        return await enrich_identity(session, symbol, body, settings)
    except IdentityError as exc:
        code = str(exc)
        status = (
            404
            if code == "identity_not_found"
            else 502
            if code in {"identity_provider_unavailable", "identity_invalid_profile"}
            else 409
        )
        raise HTTPException(status, detail=code) from None


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
