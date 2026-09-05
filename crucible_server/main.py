import uvicorn
import logging

from rich.traceback import install
from rich.logging import RichHandler

logger = logging.getLogger(__name__)

install(show_locals=True)

def main() -> None:
    """Run the Crucible server with Uvicorn for local development.

    Configures Rich-formatted logging and tracebacks, then starts Uvicorn
    against the `crucible_server.app:create_app` factory on
    `127.0.0.1:8000`. This is the entry point used when running
    `python -m crucible_server.main` directly; production deployments
    typically invoke Uvicorn/Gunicorn against the app factory instead.
    """

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                show_path=False,
            )
        ],
    )

    uvicorn.run(
        "crucible_server.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
    )


if __name__ == "__main__":
    main()
