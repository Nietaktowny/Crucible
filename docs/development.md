# Development

## Backend (`crucible`, `crucible_server`, `crucible_workspace`)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

With coverage (configured in `pyproject.toml` to measure the `crucible`
package):

```bash
pytest --cov
```

Run the API server with auto-reload:

```bash
uvicorn crucible_server.app:create_app --factory --reload
```

## Frontend (`crucible_gui`)

```bash
cd crucible_gui
npm install
```

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite dev server alone (expects a backend already running on `:8000`). |
| `npm run dev:full` | Start the backend (via a local `.venv`) and the frontend together. |
| `npm run build` | Type-check (`tsc -b`) and build the production bundle. |
| `npm run lint` | Run ESLint. |
| `npm run test` | Run the Vitest unit test suite once. |
| `npm run test:watch` | Run Vitest in watch mode. |

## Running everything with Docker instead

If you'd rather not install Python/Node locally at all, every command
above has a Docker Compose equivalent — see [Deployment](deployment.md#running-tests-in-docker).

## Project layout

```
crucible/            # engine: workflow loading, compilation, execution, built-in steps
crucible_server/     # FastAPI wrapper exposing the engine over HTTP
crucible_workspace/  # local storage: workflow files, run history, preview cache
crucible_gui/        # React frontend
docs/                # this documentation site (MkDocs)
tests/               # backend test suite (pytest)
```

## Building the docs site locally

```bash
mkdocs serve
```

Serves this site at `http://127.0.0.1:8001` with live reload
(see `mkdocs.yml` for the configured port). `mkdocs build` produces a
static `site/` directory.
