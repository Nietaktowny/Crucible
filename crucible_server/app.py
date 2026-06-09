# src/crucible_server/app.py

from fastapi import FastAPI

from crucible_server.api.routes import api_router
from crucible_server.errors import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="Crucible Server",
        version="0.1.0",
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app