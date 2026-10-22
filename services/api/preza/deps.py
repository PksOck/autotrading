from functools import lru_cache

from preza.config import get_settings
from preza.data.factory import build_router
from preza.services.bars import BarsService


@lru_cache
def get_bars_service() -> BarsService:
    settings = get_settings()
    return BarsService(build_router(settings), settings.bars_lookback_days)
