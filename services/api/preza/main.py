from fastapi import FastAPI

from preza import __version__
from preza.routes import instruments, portfolio, system, watchlist


def create_app() -> FastAPI:
    app = FastAPI(title="Preža API", version=__version__)
    app.include_router(system.router)
    app.include_router(instruments.router)
    app.include_router(portfolio.router)
    app.include_router(watchlist.router)
    return app


app = create_app()
