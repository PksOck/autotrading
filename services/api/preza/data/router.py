"""Quota-aware provider routing with fallback (BL-021)."""

import logging
from dataclasses import dataclass, field
from datetime import date

from preza.data.contract import (
    BarsProvider,
    InstrumentRef,
    NotFoundError,
    ProviderError,
    QuotaExceededError,
    normalize_bars,
)
from preza.data.quota import Quota
from preza.domain.market import BarIn

log = logging.getLogger(__name__)


@dataclass
class Route:
    provider: BarsProvider
    quota: Quota


@dataclass
class RoutedBars:
    provider: str
    bars: list[BarIn]


@dataclass
class AllProvidersFailedError(ProviderError):
    errors: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return "; ".join(f"{name}: {err}" for name, err in self.errors.items()) or "no providers"


class BarsRouter:
    """Tries providers in order. Skips exhausted quotas, falls through on any provider error."""

    def __init__(self, routes: list[Route]):
        self.routes = routes

    async def daily_bars(self, ref: InstrumentRef, start: date) -> RoutedBars:
        errors: dict[str, str] = {}
        for route in self.routes:
            name = route.provider.name
            if not route.quota.try_acquire():
                errors[name] = "quota"
                continue
            try:
                bars = normalize_bars(await route.provider.daily_bars(ref, start), start)
            except NotFoundError:
                errors[name] = "not_found"
                continue
            except QuotaExceededError:
                errors[name] = "quota"
                continue
            except ProviderError as exc:
                log.warning("provider %s failed for %s: %s", name, ref.symbol, exc)
                errors[name] = str(exc) or type(exc).__name__
                continue
            if bars:
                return RoutedBars(provider=name, bars=bars)
            errors[name] = "empty"
        raise AllProvidersFailedError(errors)
