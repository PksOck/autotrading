"""Builds the provider chain from settings: IB Gateway first (when enabled), then free fallbacks."""

from typing import cast

from preza.config import Settings
from preza.data.providers.stooq import StooqProvider
from preza.data.providers.yahoo import YahooProvider
from preza.data.quota import Quota
from preza.data.router import BarsRouter, Route


def build_router(settings: Settings) -> BarsRouter:
    routes: list[Route] = []
    if settings.ib_gateway_enabled:
        from ib_async import IB

        from preza.data.providers.ibkr import IbkrProvider, IBLike

        # IBKR pacing: max 60 historical requests per 10 minutes; keep headroom.
        provider = IbkrProvider(
            cast(IBLike, IB()), settings.ib_gateway_host, settings.ib_gateway_port
        )
        routes.append(Route(provider, Quota(50, 600)))
    if settings.yahoo_enabled:
        routes.append(Route(YahooProvider(), Quota(300, 3600)))
    if settings.stooq_enabled:
        routes.append(Route(StooqProvider(), Quota(150, 3600)))
    return BarsRouter(routes)
