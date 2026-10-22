"""Look-through exposure and overlap with the portfolio (BL-083). Pure functions.

Weights are fractions of the whole portfolio. An ETF passes its weight to the
holdings its provider lists; the rest stays "unexplained" rather than guessed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Holding:
    symbol: str
    kind: str  # "stock" or "etf"
    weight: float  # of the portfolio


@dataclass
class Exposure:
    by_symbol: dict[str, float] = field(default_factory=dict)
    unexplained: float = 0.0  # ETF weight beyond the listed holdings


@dataclass
class OverlapRow:
    symbol: str
    name: str
    weight_in_etf: float
    portfolio_exposure: float


@dataclass
class Overlap:
    rows: list[OverlapRow]
    shared_weight: float  # share of the ETF's listed holdings that you already own
    coverage: float  # share of the ETF its listed holdings explain


def base_symbol(symbol: str) -> str:
    """'ASML.AS' and 'ASML' are the same company for exposure purposes."""
    return symbol.upper().split(".")[0].replace("-", "")


def look_through(holdings: list[Holding], profiles: dict[str, list[dict[str, Any]]]) -> Exposure:
    exposure = Exposure()
    for h in holdings:
        if h.kind == "etf" and profiles.get(h.symbol):
            listed = profiles[h.symbol]
            for item in listed:
                key = base_symbol(item["symbol"])
                exposure.by_symbol[key] = (
                    exposure.by_symbol.get(key, 0.0) + h.weight * item["weight"]
                )
            exposure.unexplained += h.weight * max(0.0, 1 - sum(i["weight"] for i in listed))
        elif h.kind == "etf":
            exposure.unexplained += h.weight
        else:
            key = base_symbol(h.symbol)
            exposure.by_symbol[key] = exposure.by_symbol.get(key, 0.0) + h.weight
    return exposure


def overlap(candidate: list[dict[str, Any]], exposure: Exposure) -> Overlap:
    rows = [
        OverlapRow(
            symbol=item["symbol"],
            name=item.get("name", ""),
            weight_in_etf=item["weight"],
            portfolio_exposure=exposure.by_symbol.get(base_symbol(item["symbol"]), 0.0),
        )
        for item in candidate
    ]
    coverage = sum(r.weight_in_etf for r in rows)
    shared = sum(r.weight_in_etf for r in rows if r.portfolio_exposure > 0)
    return Overlap(
        rows=sorted(rows, key=lambda r: -r.weight_in_etf),
        shared_weight=shared / coverage if coverage else 0.0,
        coverage=coverage,
    )
