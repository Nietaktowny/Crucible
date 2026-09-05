from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crucible_server.api.routes import api_router
from crucible_server.errors import register_exception_handlers


def create_app() -> FastAPI:
    """Build and configure the Crucible FastAPI application.

    Wires up CORS (permissive for any `localhost`/`127.0.0.1` port, since
    the frontend dev server's port can shift), the domain exception
    handlers, and the versioned API router. Used as a Uvicorn app factory
    (`crucible_server.app:create_app`) so a fresh app instance is created
    per worker.

    Returns:
        FastAPI: The configured application instance.
    """
    app = FastAPI(
        title="Crucible Server",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app
