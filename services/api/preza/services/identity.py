"""Explicit per-listing company-profile enrichment; no security-type/currency inference.

Finnhub's official CompanyProfile2 schema defines currency as the currency of
company filings. It is not evidence of a listing's trading currency. Its exchange
is a display label, sometimes longer than our exchange field; never truncate it.
"""

from datetime import UTC, datetime

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from preza.config import Settings
from preza.domain.market import IdentityEnrichInput, IdentityEnrichOut
from preza.models import Instrument


class IdentityError(Exception):
    """Stable safe code, without provider response bodies or authentication values."""


class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    ticker: str
    name: str | None = None
    exchange: str | None = None
    currency: str | None = None


async def fetch_profile(
    symbol: str, settings: Settings, *, client: httpx.AsyncClient | None = None
) -> CompanyProfile:
    if not settings.finnhub_api_key:
        raise IdentityError("identity_unconfigured")
    if client is None:
        async with httpx.AsyncClient(timeout=15) as owned:
            return await fetch_profile(symbol, settings, client=owned)
    try:
        response = await client.get(
            "https://finnhub.io/api/v1/stock/profile2",
            params={"symbol": symbol},
            headers={"X-Finnhub-Token": settings.finnhub_api_key},
        )
        response.raise_for_status()
        payload = response.json()
        if not payload:
            raise IdentityError("identity_not_found")
        return CompanyProfile.model_validate(payload)
    except httpx.HTTPError:
        raise IdentityError("identity_provider_unavailable") from None
    except (ValueError, ValidationError):
        raise IdentityError("identity_invalid_profile") from None


async def enrich_identity(
    session: AsyncSession, symbol: str, body: IdentityEnrichInput, settings: Settings
) -> IdentityEnrichOut:
    row = await session.get(Instrument, body.instrument_id)
    if row is None or row.symbol != symbol.upper():
        raise IdentityError("identity_not_found")
    if row.updated_at != body.expected_updated_at:
        raise IdentityError("identity_conflict")
    count = await session.scalar(
        select(func.count()).select_from(Instrument).where(Instrument.symbol == row.symbol)
    )
    if count != 1:
        raise IdentityError("identity_ambiguous")
    profile = await fetch_profile(row.symbol, settings)
    if profile.ticker.strip().upper() != row.symbol:
        raise IdentityError("identity_symbol_mismatch")
    exchange = (profile.exchange or "").strip()
    if row.exchange and exchange and row.exchange.casefold() != exchange.casefold():
        raise IdentityError("identity_exchange_mismatch")
    # Do not hold a database lock while waiting for a provider. Recheck the version
    # after acquiring the lock, so two browser requests cannot overwrite each other.
    row = await session.scalar(
        select(Instrument)
        .where(Instrument.id == body.instrument_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if row is None or row.updated_at != body.expected_updated_at:
        raise IdentityError("identity_conflict")
    changed = []
    gaps = ["security_type_not_provided", "trading_currency_not_provided"]
    name = (profile.name or "").strip()
    if not row.name and name and len(name) <= 200:
        row.name = name
        changed.append("name")
    if not row.exchange and exchange:
        if len(exchange) <= 20:
            row.exchange = exchange
            changed.append("exchange")
        else:
            gaps.append("exchange_label_requires_mapping")
    now = datetime.now(UTC)
    if changed:
        row.source = "finnhub_profile2"
        row.updated_at = now
        await session.flush()
    return IdentityEnrichOut(
        instrument_id=row.id,
        changed_fields=changed,
        source="finnhub_profile2",
        checked_at=now,
        gaps=gaps,
    )
