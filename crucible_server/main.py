# src/crucible_server/main.py

import uvicorn


def main() -> None:
    uvicorn.run(
        "crucible_server.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
    )


if __name__ == "__main__":
    main()