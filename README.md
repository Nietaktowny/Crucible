# Crucible

**A local-first workflow engine for data transformation and reporting**, built on [Polars](https://pola.rs).

Describe a data pipeline — read a file, reshape it, join it with something
else, write the result — as a small, declarative YAML document, then run
it from the CLI, an HTTP API, or a visual workflow editor. Everything runs
on your own machine.

📖 **[Full documentation](https://nietaktowny.github.io/Crucible/)** — getting started, the step catalog, deployment, and the API reference.

```yaml
name: sales_by_country
steps:
  - key: read_csv
    parameters:
      path: sales.csv
  - key: group_by
    parameters:
      by: [country]
      aggregations:
        - column: amount
          function: sum
          alias: total_sales
  - key: write_csv
    parameters:
      path: sales_by_country.csv
```

## Quick start

The fastest way to try Crucible is with Docker — no local Python or Node
install needed:

```bash
docker compose up --build
```

- Frontend: [http://localhost:8080](http://localhost:8080)
- Backend API: [http://localhost:8000/docs](http://localhost:8000/docs)

Or run it directly:

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m crucible run --workflow first_workflow.yaml --inspect
```

See [Getting Started](https://nietaktowny.github.io/Crucible/getting-started/)
for the full walkthrough, including running the GUI from source.

## What's in this repo

| Package | Purpose |
| --- | --- |
| [`crucible`](crucible/) | The engine: workflow loading, compilation, execution, and 30+ built-in steps. |
| [`crucible_server`](crucible_server/) | A FastAPI service exposing the engine over HTTP. |
| [`crucible_workspace`](crucible_workspace/) | Local storage for workflow files, run history, and the preview cache. |
| [`crucible_gui`](crucible_gui/) | A React frontend for building and running workflows visually. |
| [`docs`](docs/) | This project's documentation site (MkDocs). |

## Running the tests

```bash
pytest                                  # backend
cd crucible_gui && npm run test         # frontend
```

...or, without installing anything locally:

```bash
docker compose run --rm backend-tests
docker compose run --rm frontend-tests
```

See [Development](https://nietaktowny.github.io/Crucible/development/) and
[Deployment](https://nietaktowny.github.io/Crucible/deployment/) for details.

## License

Apache-2.0 — see [LICENSE.md](LICENSE.md).
