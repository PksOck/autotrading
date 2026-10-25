from fastapi import FastAPI

from preza import __version__
from preza.routes import (
    analyses,
    entries,
    instruments,
    portfolio,
    proposals,
    radar,
    signals,
    system,
    theses,
    watchlist,
)


def create_app() -> FastAPI:
    app = FastAPI(title="Preža API", version=__version__)
    app.include_router(system.router)
    app.include_router(instruments.router)
    app.include_router(portfolio.router)
    app.include_router(watchlist.router)
    app.include_router(radar.router)
    app.include_router(signals.router)
    app.include_router(proposals.router)
    app.include_router(entries.router)
    app.include_router(analyses.router)
    app.include_router(theses.router)
    return app


app = create_app()
