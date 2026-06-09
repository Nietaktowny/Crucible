import uvicorn
import logging

from rich.traceback import install
from rich.logging import RichHandler

logger = logging.getLogger(__name__)

install(show_locals=True)

def main() -> None:
    
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