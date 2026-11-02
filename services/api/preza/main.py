from fastapi import FastAPI

from preza import __version__
from preza.routes import (
    analyses,
    auth,
    automation,
    backtest,
    calibration,
    dividends,
    email,
    entries,
    instruments,
    overview,
    portfolio,
    proposals,
    radar,
    signals,
    system,
    theses,
    track_record,
    watchlist,
)
from preza.security import protect
from preza.security_logging import configure_network_logging


def create_app() -> FastAPI:
    configure_network_logging()
    app = FastAPI(title="Preža API", version=__version__)
    app.middleware("http")(protect)
    app.include_router(auth.router)
    app.include_router(system.router)
    app.include_router(automation.router)
    app.include_router(backtest.router)
    app.include_router(dividends.router)
    app.include_router(email.router)
    app.include_router(instruments.router)
    app.include_router(overview.router)
    app.include_router(portfolio.router)
    app.include_router(watchlist.router)
    app.include_router(radar.router)
    app.include_router(signals.router)
    app.include_router(proposals.router)
    app.include_router(entries.router)
    app.include_router(analyses.router)
    app.include_router(theses.router)
    app.include_router(track_record.router)
    app.include_router(calibration.router)
    return app


app = create_app()
