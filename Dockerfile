# Backend image: the Crucible engine + FastAPI server (crucible_server).
#
# Build (from repo root):
#   docker build --target runtime -t crucible-backend .
# Run:
#   docker run -p 8000:8000 -v crucible-data:/data crucible-backend
#
# See docker-compose.yml for running this together with the frontend, and
# `docker compose run --rm backend-tests` for the `test` stage below.

FROM python:3.13-slim AS base

WORKDIR /app

# Only copy what the package build actually needs, so the image build is
# unaffected by whatever else happens to be sitting in the repo checkout
# (large local data files, the frontend's node_modules, etc.) and so
# setuptools' package auto-discovery (see [tool.setuptools.packages.find]
# in pyproject.toml) never sees unrelated top-level directories.
COPY pyproject.toml README.md LICENSE.md ./
COPY crucible ./crucible
COPY crucible_server ./crucible_server
COPY crucible_workspace ./crucible_workspace

RUN pip install --no-cache-dir .

# Workflows, run history and the preview cache are persisted here; mount a
# volume at this path to keep them across container restarts/upgrades.
ENV CRUCIBLE_WORKSPACE_DIR=/data
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000

FROM base AS runtime
CMD ["uvicorn", "crucible_server.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# `docker compose run --rm backend-tests` targets this stage.
FROM base AS test
RUN pip install --no-cache-dir ".[dev]"
COPY tests ./tests
CMD ["pytest"]
