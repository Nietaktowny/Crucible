# Documentation site (MkDocs). Not needed to run Crucible itself — this is
# purely for browsing/serving the docs in docs/.
#
# Build (from repo root):
#   docker build -t crucible-docs -f docs/Dockerfile .
# Run:
#   docker run -p 8001:8001 crucible-docs
#
# Or via `docker compose --profile docs up docs` (see ../docker-compose.yml).

FROM python:3.13-slim AS base

WORKDIR /app

COPY pyproject.toml README.md LICENSE.md ./
COPY crucible ./crucible
COPY crucible_server ./crucible_server
COPY crucible_workspace ./crucible_workspace
COPY docs ./docs
COPY mkdocs.yml ./

RUN pip install --no-cache-dir ".[dev]"

EXPOSE 8001

CMD ["mkdocs", "serve", "-a", "0.0.0.0:8001"]
