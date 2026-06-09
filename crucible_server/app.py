from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crucible_server.api.routes import api_router
from crucible_server.errors import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="Crucible Server",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app