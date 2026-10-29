"""Sort complete read models; unknown numeric values stay last in both directions."""

from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel


def sort_rows[T: BaseModel](
    rows: list[T], key: str | None, direction: str = "asc", q: str | None = None
) -> list[T]:
    if q:
        rows = [
            r
            for r in rows
            if q.casefold() in f"{getattr(r, 'symbol', '')} {getattr(r, 'name', '')}".casefold()
        ]
    if not key:
        return rows
    numeric = {
        "quantity",
        "market_price",
        "market_value",
        "weight_pct",
        "unrealized_pnl",
        "change_pct",
        "last_close",
        "latest_close",
        "since_added_pct",
        "target_price",
        "pe",
        "forward_pe",
        "dividend_yield_pct",
        "payout_ratio_pct",
        "ev_ebit",
        "fcf_yield",
        "roe_pct",
        "gross_margin_pct",
        "net_margin_pct",
        "revenue_growth_pct",
        "dividend_per_share",
        "ter",
        "debt_to_equity",
    }

    def value(row: T) -> Any:
        raw = getattr(row, key, None)
        if raw is None:
            raw = getattr(row, "metrics", {}).get(key)
            raw = raw.value if raw is not None else None
        if key in numeric:
            try:
                return Decimal(str(raw)) if raw is not None else None
            except InvalidOperation:
                return None
        return str(raw).casefold() if raw is not None else None

    known = [r for r in rows if value(r) is not None]
    unknown = [r for r in rows if value(r) is None]
    known.sort(
        key=lambda r: (
            str(getattr(r, "account_id", "")),
            str(getattr(r, "instrument_id", getattr(r, "id", ""))),
        )
    )
    known.sort(key=value, reverse=direction == "desc")
    if key in {
        "market_price",
        "market_value",
        "unrealized_pnl",
        "last_close",
        "latest_close",
        "target_price",
        "dividend_per_share",
    }:
        known.sort(key=lambda r: getattr(r, "currency", None) or "")
    return known + unknown
