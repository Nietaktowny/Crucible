from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crucible_server.api.routes import api_router
from crucible_server.errors import UnhandledErrorMiddleware, register_exception_handlers


def create_app() -> FastAPI:
    """Build and configure the Crucible FastAPI application.

    Wires up CORS (permissive for any `localhost`/`127.0.0.1` port, since
    the frontend dev server's port can shift), a catch-all error middleware
    so even unexpected exceptions get a CORS-friendly JSON response, the
    domain exception handlers, and the versioned API router. Used as a
    Uvicorn app factory (`crucible_server.app:create_app`) so a fresh app
    instance is created per worker.

    Returns:
        FastAPI: The configured application instance.
    """
    app = FastAPI(
        title="Crucible Server",
        version="0.1.0",
    )

    # Starlette's add_middleware() prepends, so whichever is added *last*
    # ends up outermost. UnhandledErrorMiddleware must be added first so it
    # ends up nested inside CORSMiddleware — see its docstring for why.
    app.add_middleware(UnhandledErrorMiddleware)

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
