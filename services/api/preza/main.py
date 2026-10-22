from fastapi import FastAPI

from preza import __version__
from preza.routes import system


def create_app() -> FastAPI:
    app = FastAPI(title="Preža API", version=__version__)
    app.include_router(system.router)
    return app


app = create_app()
