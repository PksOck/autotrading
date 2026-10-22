"""Staged buying ladder for an entry zone (BL-063, CMP-15). A suggestion shown in the UI only."""

from dataclasses import dataclass
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True)
class LadderLevel:
    price: Decimal
    weight: Decimal
    amount: Decimal | None = None
    quantity: Decimal | None = None


def build_ladder(
    zone_high: Decimal,
    atr: Decimal,
    stop: Decimal | None,
    weights: list[float],
    step_atr: float = 1.0,
    budget: Decimal | None = None,
) -> list[LadderLevel]:
    """Limit levels from the top of the zone down in ATR steps, never at or below the stop.

    Levels that would fall to the stop are dropped and their weight moves to the last kept level.
    With a budget, each level gets an amount and a whole-share quantity (rounded down).
    """
    step = atr * Decimal(str(step_atr))
    floor = stop + atr / 4 if stop is not None else Decimal(0)
    prices: list[Decimal] = []
    for i in range(len(weights)):
        price = (zone_high - step * i).quantize(CENT, ROUND_HALF_UP)
        if price <= floor or price <= 0:
            break
        prices.append(price)
    if not prices:
        return []
    ws = [Decimal(str(w)) for w in weights]
    kept = ws[: len(prices)]
    kept[-1] += sum(ws[len(prices) :], Decimal(0))
    levels = []
    for price, weight in zip(prices, kept, strict=True):
        amount = (budget * weight).quantize(CENT, ROUND_DOWN) if budget is not None else None
        quantity = (amount / price).to_integral_value(ROUND_DOWN) if amount is not None else None
        levels.append(LadderLevel(price=price, weight=weight, amount=amount, quantity=quantity))
    return levels
