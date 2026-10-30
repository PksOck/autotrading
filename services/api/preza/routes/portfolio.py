import uuid
from datetime import date
from typing import Annotated
from xml.etree.ElementTree import ParseError

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from preza.broker.flex import FlexError, parse_statement
from preza.config import Settings, get_settings
from preza.db import get_session
from preza.domain.portfolio import PortfolioOut
from preza.queue import enqueue
from preza.services.portfolio import get_portfolio, record_sync, store_statement
from preza.services.table_sort import sort_rows

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class Queued(BaseModel):
    job_id: str


class PortfolioImportOut(BaseModel):
    counts: dict[str, int]
    as_of: date | None


MAX_IMPORT_BYTES = 10 * 1024 * 1024


async def _read_capped(request: Request, limit: int) -> bytes:
    """Stop reading as soon as the body exceeds the limit, so oversized uploads never buffer."""
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > limit:
        raise HTTPException(413, detail="flex_too_large")
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > limit:
            raise HTTPException(413, detail="flex_too_large")
    return bytes(body)


@router.post("/import", response_model=PortfolioImportOut)
async def import_statement(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PortfolioImportOut:
    body = await _read_capped(request, MAX_IMPORT_BYTES)
    if not body.strip():
        raise HTTPException(400, detail="flex_empty")
    try:
        xml = body.decode("utf-8")
        if next(ElementTree.fromstring(xml).iter("FlexStatement"), None) is None:
            raise FlexError(None, "missing statement")
        statement = parse_statement(xml)
    except (UnicodeError, FlexError, ParseError, DefusedXmlException, ValueError):
        await record_sync(session, "flex", "failed", "flex_invalid")
        await session.commit()
        raise HTTPException(422, detail="flex_invalid") from None
    try:
        counts = await store_statement(session, statement)
    except ValueError:
        await session.rollback()
        raise HTTPException(422, detail="dividend_transaction_conflict") from None
    detail = "file: " + ", ".join(f"{key}={value}" for key, value in counts.items())
    await record_sync(session, "flex", "ok", detail)
    await session.commit()
    await enqueue(settings, "refresh_bars", job_id=f"refresh_bars:manual:{uuid.uuid4()}")
    dates = [p.report_date for p in statement.positions] + [c.report_date for c in statement.cash]
    return PortfolioImportOut(counts=counts, as_of=max(dates, default=None))


@router.get("", response_model=PortfolioOut)
async def portfolio(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    account_id: str | None = None,
    sort: str | None = None,
    direction: str = "asc",
    q: str | None = None,
) -> PortfolioOut:
    result = await get_portfolio(session, settings.base_currency, account_id)
    result.positions = sort_rows(result.positions, sort, direction, q)
    return result


@router.post("/sync", response_model=Queued, status_code=202)
async def sync(settings: Annotated[Settings, Depends(get_settings)]) -> Queued:
    if not (settings.ibkr_flex_token and settings.ibkr_flex_query_id):
        raise HTTPException(409, detail="flex_unconfigured")
    job_id = await enqueue(settings, "sync_flex", job_id=f"sync_flex:manual:{uuid.uuid4()}")
    if job_id is None:
        raise HTTPException(503, detail="queue_unavailable")
    return Queued(job_id=job_id)
